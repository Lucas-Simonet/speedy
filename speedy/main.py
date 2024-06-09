import asyncio
from starlette.applications import Starlette
from starlette.templating import Jinja2Templates
from starlette.routing import Route, WebSocketRoute, Mount
from starlette.websockets import WebSocket
from starlette.staticfiles import StaticFiles
import uvicorn
import contextlib
from asyncio import sleep as async_sleep
from time import sleep as sync_sleep
from asyncio import Queue as AsyncQueue
from concurrent.futures import ProcessPoolExecutor
from multiprocessing import Pipe
from multiprocessing.connection import Connection
import os


def generate_text(child_con: Connection):
    print("process started")
    for i in range(10):
        child_con.send("Hello, ws \n")
        sync_sleep(0.5)
    child_con.close()


templates = Jinja2Templates(directory="templates")

queue = AsyncQueue()
process_pool: ProcessPoolExecutor = ProcessPoolExecutor(max_workers=2)


async def check_queue_status():
    while True:
        # print(os.cpu_count())
        if not queue.empty():
            item = await queue.get()
            print(f"Processing item: {item}")
            result1 = await asyncio.get_event_loop().run_in_executor(process_pool, generate_text, item[0])
            result2 = await asyncio.get_event_loop().run_in_executor(process_pool, generate_text, item[1])
        else: 
            await async_sleep(1)

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


async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    parent_con_1, child_con_1 = Pipe() # https://docs.python.org/3/library/multiprocessing.html
    parent_con_2, child_con_2 = Pipe() 
 
    await queue.put((child_con_1, child_con_2 ))

    async def receive_messages():
        try:
            while True:
                data = await websocket.receive_text()
                print("Message received:", data) 
        except Exception as e:
            print(f"Receive error: {e}")
        finally:
            await websocket.close()

    async def send_messages():
        try:
            while True:
                message = await asyncio.get_event_loop().run_in_executor(None, parent_con_1.recv) # trick bc recv has no async version
                if message: 
                    await websocket.send_text(f"""{{"channel_1" : "{message}"}}""")
                message = await asyncio.get_event_loop().run_in_executor(None, parent_con_2.recv)
                if message: 
                    await websocket.send_text(f"""{{"channel_2" : "{message}"}}""")
        except Exception as e:
            print(f"Send error: {e}")
        finally:
            await websocket.close()

    await asyncio.gather(receive_messages(), send_messages())



routes = [
    Route("/", homepage),
    WebSocketRoute("/ws", websocket_endpoint),
    Mount("/static", app=StaticFiles(directory="static"), name="static"),
]

app = Starlette(debug=True, routes=routes, lifespan=lifespan)

if __name__ == "__main__":
    uvicorn.run(app)
