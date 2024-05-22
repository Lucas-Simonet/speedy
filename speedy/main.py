import asyncio
from starlette.applications import Starlette
from starlette.responses import PlainTextResponse
from starlette.templating import Jinja2Templates
from starlette.routing import Route, WebSocketRoute, Mount
from starlette.staticfiles import StaticFiles
import uvicorn
import contextlib
from anyio import sleep
import os

templates = Jinja2Templates(directory="templates")

queue = asyncio.Queue()


async def check_queue_status():
    while True:
        # print(os.cpu_count())
        if not queue.empty():
            item = await queue.get()
            print(f"Processing item: {item}")
        else:
            print("Queue is empty")
        await sleep(10)


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
    template = "index.html"
    context = {"request": request}
    return templates.TemplateResponse(template, context)



async def websocket_endpoint(websocket):
    await websocket.accept()
    await websocket.send_text("Hello, ")
    await sleep(1)
    await websocket.send_text("I'm ")
    await sleep(1)
    await websocket.send_text(" a Websocket !!")
    await websocket.close()


routes = [
    Route("/", homepage),
    WebSocketRoute("/ws", websocket_endpoint),
    Mount("/static", app=StaticFiles(directory="static"), name="static"),
]

app = Starlette(debug=True, routes=routes, lifespan=lifespan)

if __name__ == "__main__":
    uvicorn.run(app)
