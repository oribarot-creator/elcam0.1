import os, textwrap, flask, json

tpl = textwrap.dedent('''
import React, {useState, useEffect} from "react";
import ReactDOM from "react-dom/client";

const API = "/api";

function App(){
 const [name, setName] = useState("");
 if(!name) return <Login setName={setName}/>;
 return <>
   <Menu name={name}/>
   <Game name={name}/>
 </>;
}

function Login({setName}){
 const [n, setN] = useState("");
 return <div style={{textAlign:"center", marginTop:100}}>
   <h2>Enter your name</h2>
   <input value={n} onChange={e=>setN(e.target.value)} maxLength={10}/>
   <button onClick={()=> n.trim() && setName(n.trim())}>OK</button>
 </div>;
}

function Menu({name}){
 const [opts, setOpts] = useState({apples:3, hard:false});
 const update = (k,v)=>setOpts({...opts, [k]:v});
 return <div style={{textAlign:"center", margin:20}}>
   <h3>Welcome {name}</h3>
   <label>Apples:
     <select value={opts.apples} onChange={e=>update("apples", +e.target.value)}>
       {[1,3,5,7].map(x=><option key={x}>{x}</option>)}
     </select>
   </label>
   <label>Mode:
     <select value={opts.hard} onChange={e=>update("hard", e.target.value==="true")}>
       <option value={false}>NORMAL</option>
       <option value={true}>HARD</option>
     </select>
   </label>
   <button onClick={()=> window.dispatchEvent(new CustomEvent("startGame", {detail:opts}))}>
     Play Snake
   </button>
 </div>;
}
function Game({name}){
 useEffect(()=>{
   const start = async (e)=>{
     const {apples, hard} = e.detail;
     const res = await fetch(`${API}/run`, {method:"POST", headers:{"Content-Type":"application/json"},
                                            body:JSON.stringify({apples, hard, name})});
     const final = await res.json();
     await fetch(`${API}/score`, {method:"POST", headers:{"Content-Type":"application/json"},
                                  body:JSON.stringify({name, score:final.score, apples:final.apples, hard:final.hard})});
     alert("Game over – score saved!");
     window.location.reload();
   };
   window.addEventListener("startGame", start);
   return ()=> window.removeEventListener("startGame", start);
 },[name]);
 return <canvas width={750} height={750} style={{background:"#111", display:"block", margin:"20px auto"}}/>;
}

const root = ReactDOM.createRoot(document.getElementById("root"));
root.render(<App/>);
''')

def build():
   os.makedirs("static", exist_ok=True)
   with open("static/index.html", "w") as f:
       f.write('<!doctype html><html><head><meta charset="utf-8"/><title>Snake</title></head>'
               '<body><div id="root"></div><script src="bundle.js"></script></body></html>')
   with open("static/bundle.js", "w") as f:
       f.write(tpl)
if __name__ == "__main__":
   build()