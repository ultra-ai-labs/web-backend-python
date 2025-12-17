import asyncio

async def task(name):
    print(f"Task {name} starting")
    await asyncio.sleep(2)
    print(f"Task {name} completed")

async def main():
    tasks = [task(i) for i in range(5)]
    await asyncio.gather(*tasks)

asyncio.run(main())
print("All tasks completed")
