import React from "react";
import { useState, useEffect } from "react";

export function Tavili() {
    const [answer, setAnswer] = useState("");

    useEffect(() => {
        fetch("http://localhost:8000/api/get_answer")
            .then((response) => response.json())
            .then((data) => setAnswer(data.message));
    }, []);
    return <div>{answer}</div>;
}
console.log(Tavili);