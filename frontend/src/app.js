import {useState} from "react";
import Menu from "./menu";
import Game from "./Game";

function App(){
  const [name, setName] = useState("");
  if(!name) return <Login setName={setName}/>;
  return (
    <>
      <Menu name={name}/>
      <Game name={name}/>
    </>
  );
}

function Login({setName}){
  const [n, setN] = useState("");
  const start = () => {if(n.trim()) setName(n.trim())};
  return <div style={{textAlign:"center", marginTop:100}}>
    <h2>Enter your name</h2>
    <input value={n} onChange={e=>setN(e.target.value)} maxLength={10}/>
    <button onClick={start}>OK</button>
  </div>;
}
export default App;