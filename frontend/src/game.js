import {useEffect} from "react";
import {saveScore} from "./api";

export default function Game({name}){
  useEffect(()=>{
    const start = async (e)=>{
      const {apples, hard} = e.detail;
      const res = await fetch("/api/run", {
          method : "POST",
          headers: {"Content-Type":"application/json"},
          body   : JSON.stringify({apples, hard, name})
      });
      const final = await res.json();          // {score, apples, hard}
      await saveScore({name, score:final.score, apples:final.apples, hard:final.hard});
      alert("Game over – score saved!");
      window.location.reload();                // back to menu
    };
    window.addEventListener("startGame", start);
    return ()=> window.removeEventListener("startGame", start);
  },[name]);
  return null;   // we do not need a canvas – pygame opens its own window
}
