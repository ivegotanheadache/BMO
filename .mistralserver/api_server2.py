from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List, Generator
from contextlib import asynccontextmanager
import uvicorn
import logging
import json
import gc
import config
from llama_cpp import Llama

###LOGGER###
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)



############
#classi
############
class LLMConfig(BaseModel):
    verbose: bool
    model_path: str 
    n_ctx: int 
    n_threads: int
    n_batch: int
    use_mlock: bool 

class GenerateTextRequest(BaseModel):
    config: Optional[Dict[str, Any]] = None

############
#roba
############
llm_server: Optional[Llama] = None
current_config: Optional[Dict[str, Any]] = None

def cleanup_llm_server():
    global llm_server
    if llm_server is not None:
        del llm_server
        llm_server = None
    gc.collect()

@asynccontextmanager
async def lifespan(app: FastAPI):
    global llm_server, current_config
    try:
        logger.info("Starting up API server...")
        # Initialize with default config
        llm_server = Llama(**config.default_llm_config)
        current_config = config.default_llm_config
        yield
    except Exception as e:
        logger.error(f"Error during startup: {e}")
        raise
    finally:
        logger.info("Shutting down API server...")
        cleanup_llm_server()

app = FastAPI(
    title="Local Mistral LLM API Server",
    lifespan=lifespan
)


# Routes
##########
@app.get("/")
async def root():
    global llm_server, current_config
    if llm_server is not None:
        return {
            "message": "LLM API Server is running", 
            "status": "healthy",
            "current_config": current_config
        }
    return {
        "message": "LLM API Server is not running or not initialized properly", 
        "status": "error"
    }

@app.post("/llm/set")
async def configure_llm(config: LLMConfig):
    global llm_server, current_config
    try:
        # Cleanup old instance
        cleanup_llm_server()
        
        # Create new instance with config
        config_dict = config.model_dump()
        llm_server = Llama(**config_dict)
        current_config = config_dict
        
        logger.info(f"LLM server reconfigured with: {config_dict}")
        return {
            "status": "success", 
            "message": "LLM server reconfigured",
            "config": config_dict
        }
    except Exception as e:
        logger.error(f"Configuration failed: {e}")
        raise HTTPException(status_code=500, detail=f"Configuration failed: {str(e)}")

@app.get("/llm/config")
async def get_current_config():
    global current_config
    if current_config is None:
        raise HTTPException(status_code=404, detail="No configuration found")
    return {"config": current_config}

@app.post("/generate/text/stream")
async def generate_text_stream(request: GenerateTextRequest):
    global llm_server
    
    if llm_server is None:
        raise HTTPException(status_code=503, detail="LLM server not initialized")
    
    def event_stream() -> Generator[str, None, None]:
        message = ""
        try:
            # Use llama-cpp-python's create_chat_completion with streaming
            for chunk in llm_server.create_chat_completion(**request.config, stream=True):
                content = chunk["choices"][0]["delta"].get("content", "")
                if content:
                    message += content
                    chunk_data = {
                        "type": "chunk",
                        "content": content,
                        "full_message": message
                    }
                    yield f"{json.dumps(chunk_data)}\n\n"
            
        except Exception as e:
            logger.error(f"Streaming error: {e}")
            error_data = {"type": "error", "content": str(e)}
            yield f"{json.dumps(error_data)}\n\n"
    
    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "*",
        }
    )

@app.post("/llm/chat/completions")
async def create_chat_completion(options: GenerateTextRequest):
    global llm_server
    
    # Check if server is initialized
    if llm_server is None:
        raise HTTPException(status_code=503, detail="LLM server not initialized")
    
    try:
        logger.info("Request options:", options.model_dump())
        logger.info("Config:", options.model_dump()["config"])
        
        response = llm_server.create_chat_completion(**options.config)
        response =  response["choices"][0]["message"].get("content", "")
        print("Response:", response)
        return response
        
    except Exception as e:
        logger.error(f"Chat completion error: {e}")
        raise HTTPException(status_code=500, detail=f"Chat completion failed: {str(e)}")
    
@app.post("/llm/reset")
async def reset_llm():
    global llm_server, current_config
    try:
        cleanup_llm_server()
        
        # Reinitialize with default config
        llm_server = Llama(**config.default_llm_config)
        current_config = config.default_llm_config
            
        return {
            "status": "success",
            "message": "LLM server reset to default configuration",
            "config": current_config
        }
    except Exception as e:
        logger.error(f"Reset failed: {e}")
        raise HTTPException(status_code=500, detail=f"Reset failed: {str(e)}")

@app.post("/llm/generate")
async def generate_text(request: GenerateTextRequest):
    """da usare successivament eper definire azioni/agenti"""
    global llm_server
    
    if llm_server is None:
        raise HTTPException(status_code=503, detail="LLM server not initialized")
    
    try:
        # Extract prompt and other parameters
        config = request.config or {}
        prompt = config.get("prompt", "")
        
        if not prompt:
            raise HTTPException(status_code=400, detail="Prompt is required")
        
        # Use llama-cpp-python's __call__ method for text generation
        response = llm_server(
            prompt=prompt,
            max_tokens=config.get("max_tokens", 512),
            temperature=config.get("temperature", 0.7),
            top_p=config.get("top_p", 0.9),
            stop=config.get("stop", None),
            echo=config.get("echo", False)
        )
        
        return response
        
    except Exception as e:
        logger.error(f"Text generation error: {e}")
        raise HTTPException(status_code=500, detail=f"Text generation failed: {str(e)}")

if __name__ == "__main__":
    uvicorn.run(
        "api_server2:app",  # Replace with your actual filename
        host="0.0.0.0",
        port=9999,
        reload=True,
        log_level="info"
    )
