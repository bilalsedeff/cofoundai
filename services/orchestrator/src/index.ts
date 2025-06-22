
/**
 * CoFound.ai Orchestrator Service
 * Handles multi-agent orchestration using LangGraph workflows
 */

import express from 'express';
import { PubSub, Message } from '@google-cloud/pubsub';
import { SecretManagerServiceClient } from '@google-cloud/secret-manager';
import Redis from 'ioredis';
import { Pool } from 'pg';
import winston from 'winston';

// Types
interface DreamRequestData {
  project_id: string;
  request_data: {
    user_id: string;
    project_id: string;
    prompt_text: string;
    goal: string;
    tags: string[];
    advanced_options: Record<string, any>;
  };
  timestamp: string;
}

interface AgentConfig {
  name: string;
  type: string;
  system_prompt: string;
  tools: string[];
}

interface WorkflowState {
  project_id: string;
  current_phase: string;
  active_agent: string | null;
  messages: any[];
  artifacts: Record<string, any>;
  metadata: Record<string, any>;
  status: string;
}

// Logger setup
const logger = winston.createLogger({
  level: 'info',
  format: winston.format.combine(
    winston.format.timestamp(),
    winston.format.json()
  ),
  transports: [
    new winston.transports.Console(),
    new winston.transports.File({ filename: 'orchestrator.log' })
  ]
});

class OrchestratorService {
  private app: express.Application;
  private pubsub: PubSub;
  private secretClient: SecretManagerServiceClient;
  private redis: Redis;
  private dbPool: Pool;
  private agentConfigs: Map<string, AgentConfig>;
  private workflowStates: Map<string, WorkflowState>;

  constructor() {
    this.app = express();
    this.pubsub = new PubSub();
    this.secretClient = new SecretManagerServiceClient();
    this.agentConfigs = new Map();
    this.workflowStates = new Map();
    
    this.setupMiddleware();
    this.setupRoutes();
  }

  private setupMiddleware() {
    this.app.use(express.json());
    this.app.use((req, res, next) => {
      logger.info(`${req.method} ${req.path}`, { 
        ip: req.ip,
        userAgent: req.get('User-Agent')
      });
      next();
    });
  }

  private setupRoutes() {
    this.app.get('/health', (req, res) => {
      res.json({
        status: 'healthy',
        timestamp: new Date().toISOString(),
        service: 'orchestrator'
      });
    });

    this.app.post('/api/workflow/trigger', async (req, res) => {
      try {
        const { project_id, workflow_type = 'develop_app' } = req.body;
        
        if (!project_id) {
          return res.status(400).json({ error: 'project_id is required' });
        }

        await this.triggerWorkflow(project_id, workflow_type);
        
        res.json({
          status: 'triggered',
          project_id,
          workflow_type
        });
      } catch (error) {
        logger.error('Error triggering workflow:', error);
        res.status(500).json({ error: 'Internal server error' });
      }
    });

    this.app.get('/api/workflow/:project_id/status', async (req, res) => {
      try {
        const { project_id } = req.params;
        const state = this.workflowStates.get(project_id);
        
        if (!state) {
          return res.status(404).json({ error: 'Workflow not found' });
        }

        res.json(state);
      } catch (error) {
        logger.error('Error getting workflow status:', error);
        res.status(500).json({ error: 'Internal server error' });
      }
    });
  }

  async initialize() {
    try {
      // Initialize database connection
      await this.initializeDatabase();
      
      // Initialize Redis connection
      await this.initializeRedis();
      
      // Initialize agent configurations
      await this.initializeAgentConfigs();
      
      // Start Pub/Sub subscribers
      await this.startSubscribers();
      
      logger.info('Orchestrator service initialized successfully');
    } catch (error) {
      logger.error('Failed to initialize orchestrator service:', error);
      throw error;
    }
  }

  private async initializeDatabase() {
    const projectId = process.env.GOOGLE_CLOUD_PROJECT;
    const environment = process.env.ENVIRONMENT || 'dev';
    
    const secretName = `projects/${projectId}/secrets/db-connection-${environment}/versions/latest`;
    const [version] = await this.secretClient.accessSecretVersion({ name: secretName });
    const dbConfig = JSON.parse(version.payload?.data?.toString() || '{}');
    
    this.dbPool = new Pool({
      host: dbConfig.host,
      database: dbConfig.database,
      user: dbConfig.username,
      password: dbConfig.password,
      max: 10,
      idleTimeoutMillis: 30000,
      connectionTimeoutMillis: 2000,
    });

    // Test connection
    const client = await this.dbPool.connect();
    await client.query('SELECT NOW()');
    client.release();
    
    logger.info('Database connection established');
  }

  private async initializeRedis() {
    const projectId = process.env.GOOGLE_CLOUD_PROJECT;
    const environment = process.env.ENVIRONMENT || 'dev';
    
    const secretName = `projects/${projectId}/secrets/redis-connection-${environment}/versions/latest`;
    const [version] = await this.secretClient.accessSecretVersion({ name: secretName });
    const redisConfig = JSON.parse(version.payload?.data?.toString() || '{}');
    
    this.redis = new Redis({
      host: redisConfig.host,
      port: redisConfig.port,
      retryDelayOnFailover: 100,
      maxRetriesPerRequest: 3,
    });
    
    // Test connection
    await this.redis.ping();
    
    logger.info('Redis connection established');
  }

  private async initializeAgentConfigs() {
    // Define agent configurations for LangGraph workflow
    const agents: AgentConfig[] = [
      {
        name: 'Planner',
        type: 'planning',
        system_prompt: 'You are a planning agent that breaks down requirements into actionable tasks.',
        tools: ['task_breakdown', 'requirement_analysis']
      },
      {
        name: 'Architect',
        type: 'architecture',
        system_prompt: 'You are an architecture agent that designs system architecture and technical specifications.',
        tools: ['architecture_design', 'tech_stack_selection']
      },
      {
        name: 'Developer',
        type: 'development',
        system_prompt: 'You are a developer agent that writes clean, maintainable code.',
        tools: ['code_generation', 'code_review']
      },
      {
        name: 'Tester',
        type: 'testing',
        system_prompt: 'You are a testing agent that creates comprehensive test suites.',
        tools: ['test_generation', 'test_execution']
      },
      {
        name: 'Reviewer',
        type: 'review',
        system_prompt: 'You are a code review agent that ensures quality and best practices.',
        tools: ['code_analysis', 'quality_check']
      },
      {
        name: 'Documentor',
        type: 'documentation',
        system_prompt: 'You are a documentation agent that creates clear, helpful documentation.',
        tools: ['doc_generation', 'doc_formatting']
      }
    ];

    agents.forEach(agent => {
      this.agentConfigs.set(agent.name, agent);
    });

    logger.info(`Initialized ${agents.length} agent configurations`);
  }

  private async startSubscribers() {
    const projectId = process.env.GOOGLE_CLOUD_PROJECT;
    const environment = process.env.ENVIRONMENT || 'dev';
    
    // Subscribe to dream-requested topic
    const dreamRequestedSub = this.pubsub.subscription(`dream-requested-sub-${environment}`);
    dreamRequestedSub.on('message', this.handleDreamRequested.bind(this));
    dreamRequestedSub.on('error', error => {
      logger.error('Dream requested subscription error:', error);
    });

    logger.info('Pub/Sub subscribers started');
  }

  private async handleDreamRequested(message: Message) {
    try {
      const data: DreamRequestData = JSON.parse(message.data.toString());
      logger.info('Received dream request:', { project_id: data.project_id });

      // Initialize workflow state
      const workflowState: WorkflowState = {
        project_id: data.project_id,
        current_phase: 'dream',
        active_agent: 'Planner',
        messages: [],
        artifacts: {},
        metadata: {
          request_data: data.request_data,
          started_at: new Date().toISOString()
        },
        status: 'processing'
      };

      this.workflowStates.set(data.project_id, workflowState);

      // Process with LangGraph workflow
      await this.processWithLangGraph(data.project_id, data.request_data);

      message.ack();
    } catch (error) {
      logger.error('Error handling dream request:', error);
      message.nack();
    }
  }

  private async processWithLangGraph(projectId: string, requestData: any) {
    try {
      logger.info('Starting LangGraph workflow processing', { project_id: projectId });

      const state = this.workflowStates.get(projectId);
      if (!state) {
        throw new Error('Workflow state not found');
      }

      // Simulate LangGraph workflow execution
      const phases = [
        { name: 'dream', agent: 'Planner', duration: 2000 },
        { name: 'maturation', agent: 'Architect', duration: 3000 },
        { name: 'assemble', agent: 'Developer', duration: 4000 },
        { name: 'prototype', agent: 'Developer', duration: 5000 },
        { name: 'feedback', agent: 'Tester', duration: 3000 },
        { name: 'iterate', agent: 'Developer', duration: 4000 },
        { name: 'validate', agent: 'Reviewer', duration: 3000 },
        { name: 'golive', agent: 'Documentor', duration: 2000 },
        { name: 'evolve', agent: 'Planner', duration: 2000 }
      ];

      for (const phase of phases) {
        state.current_phase = phase.name;
        state.active_agent = phase.agent;
        
        // Update state in Redis
        await this.redis.setex(
          `workflow_state:${projectId}`,
          3600,
          JSON.stringify(state)
        );

        // Simulate processing time
        await new Promise(resolve => setTimeout(resolve, phase.duration));

        // Add phase completion to artifacts
        state.artifacts[phase.name] = {
          completed_at: new Date().toISOString(),
          agent: phase.agent,
          status: 'completed'
        };

        logger.info(`Completed phase: ${phase.name}`, { project_id: projectId });
      }

      state.status = 'completed';
      state.metadata.completed_at = new Date().toISOString();

      // Final state update
      await this.redis.setex(
        `workflow_state:${projectId}`,
        3600,
        JSON.stringify(state)
      );

      // Publish completion event
      await this.publishWorkflowCompleted(projectId, state);

      logger.info('LangGraph workflow completed', { project_id: projectId });

    } catch (error) {
      logger.error('Error in LangGraph workflow:', error);
      
      const state = this.workflowStates.get(projectId);
      if (state) {
        state.status = 'error';
        state.metadata.error = error.message;
        await this.redis.setex(
          `workflow_state:${projectId}`,
          3600,
          JSON.stringify(state)
        );
      }
    }
  }

  private async publishWorkflowCompleted(projectId: string, state: WorkflowState) {
    try {
      const projectIdEnv = process.env.GOOGLE_CLOUD_PROJECT;
      const environment = process.env.ENVIRONMENT || 'dev';
      const topicName = `blueprint-generated-${environment}`;
      
      const messageData = JSON.stringify({
        project_id: projectId,
        workflow_state: state,
        timestamp: new Date().toISOString()
      });

      await this.pubsub.topic(topicName).publishMessage({
        data: Buffer.from(messageData)
      });

      logger.info('Published workflow completion event', { project_id: projectId });
    } catch (error) {
      logger.error('Error publishing workflow completion:', error);
    }
  }

  async triggerWorkflow(projectId: string, workflowType: string) {
    logger.info('Triggering workflow', { project_id: projectId, workflow_type: workflowType });
    
    // Implementation for manual workflow triggering
    const requestData = {
      user_id: 'manual',
      project_id: projectId,
      prompt_text: 'Manual workflow trigger',
      goal: 'prototype',
      tags: [],
      advanced_options: {}
    };

    await this.processWithLangGraph(projectId, requestData);
  }

  start(port: number = 3001) {
    this.app.listen(port, '0.0.0.0', () => {
      logger.info(`Orchestrator service listening on port ${port}`);
    });
  }
}

// Initialize and start the service
async function main() {
  const service = new OrchestratorService();
  
  try {
    await service.initialize();
    service.start();
  } catch (error) {
    logger.error('Failed to start orchestrator service:', error);
    process.exit(1);
  }

  // Graceful shutdown
  process.on('SIGTERM', async () => {
    logger.info('Received SIGTERM, shutting down gracefully');
    process.exit(0);
  });

  process.on('SIGINT', async () => {
    logger.info('Received SIGINT, shutting down gracefully');
    process.exit(0);
  });
}

if (require.main === module) {
  main();
}

export default OrchestratorService;
