async function detectURL(){

    const url=document.getElementById("url").value;

    if(url===""){

        alert("Please enter a website URL.");

        return;

    }

    let formData=new FormData();

    formData.append("url",url);

    const response=await fetch("/predict",{

        method:"POST",

        body:formData

    });

    const data=await response.json();

    showResult(data);

}
function showResult(data){

    const tableBody=document.querySelector("#resultTable tbody");

    tableBody.innerHTML="";

    let phishingCount=0;

    for(let model in data){

        let prediction=data[model].prediction;

        let confidence=data[model].confidence;

        if(prediction==="Phishing") phishingCount++;

        let row=`
        <tr>

        <td>${model}</td>

        <td class="${prediction==="Safe" ? "safe-text":"phishing-text"}">

        ${prediction}

        </td>

        <td>${confidence != null ? confidence + "%" : "N/A"}</td>

        </tr>
        `;

        tableBody.innerHTML+=row;

    }

    const card=document.getElementById("resultCard");

    card.classList.remove("hidden","safe","phishing");

    if(phishingCount>=2){

        card.classList.add("phishing");

        document.getElementById("mainPrediction").innerHTML="🚨 PHISHING WEBSITE";

        document.getElementById("description").innerHTML=
        "Warning! Multiple machine learning models classified this website as phishing.";

    }

    else{

        card.classList.add("safe");

        document.getElementById("mainPrediction").innerHTML="✅ SAFE WEBSITE";

        document.getElementById("description").innerHTML=
        "Most machine learning models classified this website as safe.";

    }

}