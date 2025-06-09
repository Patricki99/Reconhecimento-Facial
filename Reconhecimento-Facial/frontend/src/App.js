import React, { useRef, useState } from "react";
import "./App.css";

function App() {
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const [capturedImage, setCapturedImage] = useState(null);
  const [response, setResponse] = useState(null);

  const startCamera = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ video: true });
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        videoRef.current.play();
      }
    } catch (error) {
      alert("Erro ao acessar a câmera: " + error.message);
    }
  };

  const captureImage = () => {
    const video = videoRef.current;
    const canvas = canvasRef.current;
    const context = canvas.getContext("2d");
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    context.drawImage(video, 0, 0, canvas.width, canvas.height);

    const dataURL = canvas.toDataURL("image/jpeg");
    setCapturedImage(dataURL);
  };

  const sendToServer = async () => {
    if (!capturedImage) return;

    const blob = await (await fetch(capturedImage)).blob();
    const formData = new FormData();
    formData.append("image", blob, "captured.jpg");

    try {
      const res = await fetch("http://127.0.0.1:5000/verify", {
        method: "POST",
        body: formData,
      });

      const data = await res.json();
      setResponse(data);
    } catch (error) {
      alert("Erro ao enviar imagem: " + error.message);
    }
  };

  return (
    <div className="app-container">
      <h1>Reconhecimento Facial</h1>
      <div className="video-container">
        <video ref={videoRef} autoPlay playsInline />
      </div>
      <button onClick={startCamera}>Ativar Câmera</button>
      <button onClick={captureImage}>Capturar Imagem</button>
      <button onClick={sendToServer}>Enviar para Verificação</button>

      <canvas ref={canvasRef} style={{ display: "none" }}></canvas>

      {capturedImage && (
        <div className="preview">
          <h2>Imagem Capturada</h2>
          <img src={capturedImage} alt="capturada" />
        </div>
      )}

      {response && (
        <div className="response-box">
          <h2>Resposta do Servidor:</h2>
          <pre>{JSON.stringify(response, null, 2)}</pre>
        </div>
      )}
    </div>
  );
}

export default App;
