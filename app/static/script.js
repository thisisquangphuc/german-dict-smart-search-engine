async function lookupWord() {
    const word = document.getElementById("wordInput").value;
    const res = await fetch(`/api/lookup?word=${word}`);
    const data = await res.json();

    let resultHTML = `
      <h3>Results for "${data.word}"</h3>
      <pre>${JSON.stringify(data.pons, null, 2)}</pre>
      <h4>Verbformen snippet:</h4>
      <pre>${data.verbformen_html}</pre>
    `;

    if (data.verb_image_url) {
        resultHTML += `<h4>Image:</h4><img src="${data.verb_image_url}" alt="Hint Image" style="max-width: 600px;">`;
    }

    document.getElementById("result").innerHTML = resultHTML;
}