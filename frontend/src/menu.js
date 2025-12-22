import {useState} from "react";
export default function Menu({name}){
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