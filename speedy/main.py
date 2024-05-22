import asyncio
from starlette.applications import Starlette
from starlette.responses import PlainTextResponse
from starlette.routing import Route, WebSocketRoute
import uvicorn
import contextlib
from anyio import sleep, create_task_group, run
queue = asyncio.Queue()



async def check_queue_status():
    while True:
        if not queue.empty():
            item = await queue.get()
            print(f"Processing item: {item}")
        else:
            print("Queue is empty")
        await sleep(1)

@contextlib.asynccontextmanager
async def lifespan(app):
    async with asyncio.TaskGroup() as task_group:
        print("Running queue emptying task")
        task = task_group.create_task(check_queue_status())    
        try:    
            yield
        finally:
            task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            print("Background task cancelled")
        print("Run on shutdown!")


async def homepage(request):
    await queue.put("homepage")
    return PlainTextResponse('Hello, world!')

def user_me(request):
    username = "John Doe"
    return PlainTextResponse('Hello, %s!' % username)

def user(request):
    username = request.path_params['username']
    return PlainTextResponse('Hello, %s!' % username)

async def websocket_endpoint(websocket):
    await websocket.accept()
    await websocket.send_text('Hello, websocket!')
    await websocket.close()



routes = [
    Route('/', homepage),
    Route('/user/me', user_me),
    Route('/user/{username}', user),
    WebSocketRoute('/ws', websocket_endpoint),
]

app = Starlette(debug=True, routes=routes, lifespan=lifespan)

if __name__ == "__main__":
    uvicorn.run(app)