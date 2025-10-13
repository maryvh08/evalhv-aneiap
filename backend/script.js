document.getElementById("uploadForm").addEventListener("submit", async (e) => {
  e.preventDefault();

  const formData = new FormData();
  formData.append("nombre", document.getElementById("nombre").value);
  formData.append("capitulo", document.getElementById("capitulo").value);
  formData.append("cargo", document.getElementById("cargo").value);
  formData.append("pdf", document.getElementById("pdf").files[0]);

  const resultDiv = document.getElementById("result");
  resultDiv.innerHTML = "⏳ Analizando hoja de vida...";

  const response = await fetch("https://tu-api-backend.vercel.app/analizar", {
    method: "POST",
    body: formData
  });

  const data = await response.json();
  resultDiv.innerHTML = `<h3>Resultado</h3><pre>${JSON.stringify(data, null, 2)}</pre>`;
});
document.getElementById("uploadForm").addEventListener("submit", async (e) => {
  e.preventDefault();

  const formData = new FormData();
  formData.append("nombre", document.getElementById("nombre").value);
  formData.append("capitulo", document.getElementById("capitulo").value);
  formData.append("cargo", document.getElementById("cargo").value);
  formData.append("pdf", document.getElementById("pdf").files[0]);

  const resultDiv = document.getElementById("result");
  resultDiv.innerHTML = "⏳ Analizando hoja de vida...";

  const response = await fetch("https://tu-api-backend.vercel.app/analizar", {
    method: "POST",
    body: formData
  });

  const data = await response.json();
  resultDiv.innerHTML = `<h3>Resultado</h3><pre>${JSON.stringify(data, null, 2)}</pre>`;
});
