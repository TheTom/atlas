import asyncio, importlib.util, json, pathlib, sys
import aiohttp
p=pathlib.Path(sys.argv[1]);s=importlib.util.spec_from_file_location("frozen",p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);m._seq=899999
async def main():
 async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(limit=0,force_close=True)) as session:
  result=await m.run_rep(session,"http://127.0.0.1:8890/v1/chat/completions",sys.argv[2],16,1024,1)
 pathlib.Path(sys.argv[3]).write_text(json.dumps(result,indent=2)+"\n")
asyncio.run(main())
