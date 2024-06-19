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
from starlette.endpoints import WebSocketEndpoint
from speedy.text_generator_service import generate_text
from huggingface_hub import hf_hub_download
from llama_cpp import Llama


def generate_text_1(child_con: Connection):
    print("process started")
    try:
        for i in range(20):
            child_con.send("Hello, ws 1 !")
            sync_sleep(0.6)
    except BrokenPipeError as e:
        return


def generate_text_2(child_con: Connection):
    print("process started")
    try:
        for i in range(20):
            child_con.send("Hello, ws 2 !")
            sync_sleep(0.2)
    except BrokenPipeError as e:
        return


templates = Jinja2Templates(directory="templates")

queue = AsyncQueue()
process_pool: ProcessPoolExecutor = ProcessPoolExecutor(max_workers=2)


async def check_queue_status():
    while True:
        # print(os.cpu_count())
        if not queue.empty():
            item = await queue.get()
            print(f"Processing item: {item}")
            asyncio.get_event_loop().run_in_executor(
                process_pool, generate_text_1, item[0]
            )
            asyncio.get_event_loop().run_in_executor(
                process_pool, generate_text_2, item[1]
            )
        else:
            await async_sleep(1)


@contextlib.asynccontextmanager
async def lifespan(app):
    async with asyncio.TaskGroup() as task_group:
        print("Downloading GGUH files")
        hf_hub_download(repo_id="microsoft/Phi-3-mini-4k-instruct-gguf", filename="Phi-3-mini-4k-instruct-q4.gguf")
        print("Running queue emptying task")
        task = task_group.create_task(check_queue_status())
        try:
            yield
        finally:
            task.cancel()
            tasks = asyncio.all_tasks()
            for task in tasks:
                task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            print("Background task cancelled")

        print("Run on shutdown !")


async def homepage(request):
    template = "index.html"
    context = {"request": request}
    return templates.TemplateResponse(template, context)


async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    stop_event = asyncio.Event()
    (
        parent_con_1,
        child_con_1,
    ) = Pipe()  # https://docs.python.org/3/library/multiprocessing.html

    parent_con_2, child_con_2 = Pipe()

    async def receive_messages():
        try:
            while not stop_event.is_set():
                data = await websocket.receive()
                if data["type"] == "websocket.disconnect":
                    print(f"setting event on stop : {data}")
                    stop_event.set()
                else:
                    await queue.put((child_con_1, child_con_2))
        except Exception as e:
            print(e)
            stop_event.set()
            return

    async def send_messages_1():
        try:
            while not stop_event.is_set():
                message = await asyncio.get_event_loop().run_in_executor(
                    None, parent_con_1.recv
                )  # trick bc recv has no async version
                if message:
                    await websocket.send_text(f"""{{"channel_1" : "{message}"}}""")
        except Exception as e:
            print(e)
            stop_event.set()
            return

    async def send_messages_2():
        try:
            while not stop_event.is_set():
                message = await asyncio.get_event_loop().run_in_executor(
                    None, parent_con_2.recv
                )
                if message:
                    await websocket.send_text(f"""{{"channel_2" : "{message}"}}""")
        except Exception as e:
            print(e)
            stop_event.set()
            return

    try:
        await asyncio.gather(receive_messages(), send_messages_1(), send_messages_2())
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        parent_con_1.close()
        parent_con_2.close()
        child_con_1.close()
        child_con_2.close()
        await websocket.close()


routes = [
    Route("/", homepage),
    WebSocketRoute("/ws", websocket_endpoint),
    Mount("/static", app=StaticFiles(directory="static"), name="static"),
]

app = Starlette(debug=True, routes=routes, lifespan=lifespan)


if __name__ == "__main__":
    uvicorn.run("main:app", reload=True)
