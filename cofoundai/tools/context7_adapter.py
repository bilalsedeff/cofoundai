"""
CoFound.ai Context7 Adapter

This module provides an adapter for integrating the Context7 library documentation 
functionality with CoFound.ai agents.
"""

from typing import Dict, Any, List, Optional
import logging
import json
import os
from pathlib import Path

# Create a logger for the Context7 adapter
logger = logging.getLogger("context7_adapter")

class Context7Adapter:
    """
    Adapter class for integrating Context7 functionality with CoFound.ai.
    
    This adapter provides methods for:
    - Resolving library IDs
    - Fetching library documentation
    - Caching documentation for offline use
    """
    
    def __init__(self, cache_dir: Optional[str] = None):
        """
        Initialize the Context7 adapter.
        
        Args:
            cache_dir: Directory to cache documentation (default: "data/context7_cache")
        """
        self.cache_dir = cache_dir or os.path.join("data", "context7_cache")
        os.makedirs(self.cache_dir, exist_ok=True)
        self.logger = logger
        self.logger.info(f"Context7Adapter initialized with cache directory: {self.cache_dir}")
        
        # Dictionary to store context7 compatible library IDs
        self.library_ids = {
            "react": "vercel/nextjs",
            "next.js": "vercel/nextjs",
            "nextjs": "vercel/nextjs",
            "tensorflow": "tensorflow/tensorflow",
            "pytorch": "pytorch/pytorch",
            "fastapi": "tiangolo/fastapi",
            "langchain": "langchain-ai/langchain",
            "mongodb": "mongodb/docs",
            "postgres": "postgres/postgres",
            "postgresql": "postgres/postgres",
            "django": "django/django",
            "flask": "pallets/flask",
            "numpy": "numpy/numpy",
            "pandas": "pandas-dev/pandas",
            "scikit-learn": "scikit-learn/scikit-learn",
            "sklearn": "scikit-learn/scikit-learn",
        }
        
    def resolve_library_id(self, library_name: str) -> Optional[str]:
        """
        Resolve a general library name to a Context7-compatible library ID.
        
        Args:
            library_name: Generic library name
            
        Returns:
            Context7-compatible library ID if available, otherwise None
        """
        library_name_lower = library_name.lower()
        
        # Check if we have a direct mapping
        if library_name_lower in self.library_ids:
            resolved_id = self.library_ids[library_name_lower]
            self.logger.info(f"Resolved library '{library_name}' to ID: {resolved_id}")
            return resolved_id
            
        # Try to find a partial match
        for key, value in self.library_ids.items():
            if key in library_name_lower or library_name_lower in key:
                self.logger.info(f"Partial match: resolved library '{library_name}' to ID: {value}")
                return value
                
        # Simulate contacting Context7 API
        self.logger.warning(f"Could not resolve library name: {library_name}")
        return None
        
    def get_library_docs(self, 
                         context7_compatible_library_id: str, 
                         topic: Optional[str] = None, 
                         tokens: int = 5000) -> Dict[str, Any]:
        """
        Fetch documentation for a Context7-compatible library ID.
        
        Args:
            context7_compatible_library_id: Library ID in Context7-compatible format
            topic: Optional topic to focus documentation on
            tokens: Maximum number of tokens to retrieve
            
        Returns:
            Dictionary with documentation data
        """
        # Check cache first
        cache_key = f"{context7_compatible_library_id}_{topic or 'general'}_{tokens}"
        cache_file = os.path.join(self.cache_dir, f"{cache_key.replace('/', '_')}.json")
        
        if os.path.exists(cache_file):
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    cached_data = json.load(f)
                self.logger.info(f"Loaded documentation from cache for {context7_compatible_library_id}")
                return cached_data
            except Exception as e:
                self.logger.error(f"Error loading cache: {e}")
                
        # Simulate fetching from Context7 API
        owner, repo = context7_compatible_library_id.split('/')
        
        # Generate fake documentation for testing
        documentation = {
            "libraryId": context7_compatible_library_id,
            "owner": owner,
            "repo": repo,
            "topic": topic or "general",
            "content": self._generate_fake_docs(context7_compatible_library_id, topic),
            "tokenCount": tokens,
            "retrievedAt": "2025-05-22T12:00:00Z"
        }
        
        # Cache the result
        try:
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(documentation, f, indent=2)
            self.logger.info(f"Cached documentation for {context7_compatible_library_id}")
        except Exception as e:
            self.logger.error(f"Error caching documentation: {e}")
            
        return documentation
    
    def _generate_fake_docs(self, library_id: str, topic: Optional[str] = None) -> str:
        """
        Generate fake documentation for testing purposes.
        
        Args:
            library_id: Context7-compatible library ID
            topic: Optional topic to focus on
            
        Returns:
            Generated documentation text
        """
        owner, repo = library_id.split('/')
        
        if repo == "nextjs":
            if topic == "routing":
                return """
# Next.js Routing

Next.js has a file-system based router built on the concept of pages.

When a file is added to the `pages` directory, it's automatically available as a route.

## Basic Routing

- `pages/index.js` → `/`
- `pages/about.js` → `/about`
- `pages/blog/[slug].js` → `/blog/:slug` (Dynamic route)

## Dynamic Routes

To match a dynamic segment, you can use the bracket syntax:

```jsx
// pages/blog/[slug].js
import { useRouter } from 'next/router'

export default function Post() {
  const router = useRouter()
  const { slug } = router.query
  
  return <p>Post: {slug}</p>
}
```

## Nested Routes

You can create nested routes by creating nested folder structures:

- `pages/blog/index.js` → `/blog`
- `pages/blog/first-post.js` → `/blog/first-post`
- `pages/dashboard/settings/username.js` → `/dashboard/settings/username`

## Catch-all Routes

To match multiple path segments, you can use `...` inside the brackets:

```jsx
// pages/blog/[...slug].js
import { useRouter } from 'next/router'

export default function BlogPosts() {
  const router = useRouter()
  const { slug } = router.query
  
  // slug is an array
  return <p>Post: {slug.join('/')}</p>
}
```
"""
            elif topic == "data fetching":
                return """
# Next.js Data Fetching

Next.js provides multiple ways to fetch data for your pages:

## getStaticProps

```jsx
// This function runs at build time in production
export async function getStaticProps() {
  const res = await fetch('https://api.example.com/data')
  const data = await res.json()
  
  return {
    props: { data }, // will be passed to the page component as props
  }
}

export default function Home({ data }) {
  return <div>{data.title}</div>
}
```

## getServerSideProps

```jsx
// This function runs on every request
export async function getServerSideProps() {
  const res = await fetch('https://api.example.com/data')
  const data = await res.json()
  
  return {
    props: { data }, // will be passed to the page component as props
  }
}
```

## Client-side Fetching with SWR

```jsx
import useSWR from 'swr'

const fetcher = (...args) => fetch(...args).then(res => res.json())

function Profile() {
  const { data, error } = useSWR('/api/user', fetcher)
  
  if (error) return <div>Failed to load</div>
  if (!data) return <div>Loading...</div>
  
  return <div>Hello {data.name}!</div>
}
```
"""
            else:
                return f"""
# Next.js Documentation

Next.js is a React framework that enables functionality such as server-side rendering, static site generation, API routes, and more.

## Getting Started

```bash
npx create-next-app@latest
# or
yarn create next-app
```

## Key Features

- File-system based routing
- API Routes
- Built-in CSS and Sass support
- Fast Refresh
- Static Generation (SSG) and Server-side Rendering (SSR)
- Incremental Static Regeneration (ISR)
- Image Optimization
- Internationalization

## Basic Page Structure

```jsx
// pages/index.js
export default function Home() {{
  return (
    <div>
      <h1>Welcome to Next.js!</h1>
    </div>
  )
}}
```

## Learn More

Visit [https://nextjs.org/docs](https://nextjs.org/docs) to learn more about Next.js.
"""
        
        elif repo == "fastapi":
            return """
# FastAPI Documentation

FastAPI is a modern, fast (high-performance), web framework for building APIs with Python 3.7+ based on standard Python type hints.

## Key Features

- Fast: Very high performance, on par with NodeJS and Go
- Fast to code: Increase the speed to develop features by about 200% to 300%
- Fewer bugs: Reduce about 40% of human (developer) induced errors
- Intuitive: Great editor support. Completion everywhere. Less time debugging
- Easy: Designed to be easy to use and learn. Less time reading docs
- Short: Minimize code duplication. Multiple features from each parameter declaration
- Robust: Get production-ready code. With automatic interactive documentation
- Standards-based: Based on (and fully compatible with) the open standards for APIs: OpenAPI and JSON Schema

## Quick Start

```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.get("/items/{item_id}")
def read_item(item_id: int, q: str = None):
    return {"item_id": item_id, "q": q}
```

## Run the Application

```bash
uvicorn main:app --reload
```

Visit http://127.0.0.1:8000/docs for the interactive API documentation.
"""
        
        # Default documentation for other libraries
        return f"""
# {repo.capitalize()} Documentation

This is a simulated documentation for {library_id}.

## Installation

```bash
pip install {repo.lower()}
# or
npm install {repo.lower()}
```

## Basic Usage

```python
# Python example
import {repo.lower()}

# Your code here
```

```javascript
// JavaScript example
const myModule = require('{repo.lower()}');

// Your code here
```

## API Reference

Please refer to the official documentation for complete API reference.

## Learn More

Visit the official documentation for more information.
"""
    
    def search_documentation(self, query: str, library_ids: List[str]) -> Dict[str, Any]:
        """
        Search across documentation from multiple libraries.
        
        Args:
            query: Search query
            library_ids: List of Context7-compatible library IDs to search in
            
        Returns:
            Search results
        """
        self.logger.info(f"Searching for '{query}' across {len(library_ids)} libraries")
        
        results = []
        for library_id in library_ids:
            # Get documentation for the library
            docs = self.get_library_docs(library_id)
            
            # Simulate search by basic substring match (in a real implementation, 
            # this would use semantic search or better text matching)
            content = docs.get("content", "")
            if query.lower() in content.lower():
                # Find the paragraph containing the query
                paragraphs = content.split('\n\n')
                matching_paragraphs = [p for p in paragraphs if query.lower() in p.lower()]
                
                for p in matching_paragraphs:
                    results.append({
                        "libraryId": library_id,
                        "content": p,
                        "score": 0.85,  # Simulated relevance score
                        "source": f"{library_id} documentation"
                    })
        
        return {
            "query": query,
            "results": results,
            "totalResults": len(results)
        }
    
    def clear_cache(self) -> None:
        """
        Clear the documentation cache.
        """
        cache_files = [f for f in os.listdir(self.cache_dir) if f.endswith('.json')]
        for file in cache_files:
            try:
                os.remove(os.path.join(self.cache_dir, file))
            except Exception as e:
                self.logger.error(f"Error removing cache file {file}: {e}")
        
        self.logger.info(f"Cleared {len(cache_files)} cache files")

# Example usage
if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    # Create adapter
    adapter = Context7Adapter()
    
    # Resolve a library ID
    lib_id = adapter.resolve_library_id("next.js")
    print(f"Resolved library ID: {lib_id}")
    
    # Get documentation
    docs = adapter.get_library_docs(lib_id, topic="routing")
    print(f"Retrieved documentation with {len(docs['content'])} characters")
    
    # Search documentation
    search_results = adapter.search_documentation("dynamic routes", [lib_id])
    print(f"Found {len(search_results['results'])} search results") 