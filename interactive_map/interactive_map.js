"use strict";

function readExcelFile(url) {
    return new Promise((resolve, reject) => {
        let xhr = new XMLHttpRequest();
        xhr.open("GET", url, true);
        xhr.responseType = "arraybuffer";
        xhr.onload = () => {
            if (xhr.status === 200) {
                resolve(xhr.response);
            } else {
                reject(xhr.statusText);
            }
        }
        xhr.onerror = () => reject(xhr.statusText);
        xhr.send();
    });
}

async function main() {
    try {
        let excelFilePath = "interactive_map_data.xlsx";
        const arrayBuffer = await readExcelFile(excelFilePath);
        let data = new Uint8Array(arrayBuffer);
        let arr = [];
        for(let i = 0; i !== data.length; i++) {
            arr[i] = String.fromCharCode(data[i]);
        }
        const bStr = arr.join("");
        const workbook = XLSX.read(bStr, {type: "binary"});
        const sheet = workbook.Sheets[workbook.SheetNames[0]];

        const sizeMultiplier = 0.6;
        const img = $("#burnoutmap");
        img.height(img.height() * sizeMultiplier); // Changing only height maintains aspect ratio
        img.removeAttr("hidden");

        let imageMap = $("#events");
        const areaRadius = 7 * sizeMultiplier;
        let row = 2;
        while (sheet[`A${row}`]) {
            const eventName = sheet[`A${row}`].v;
            const xCoord = sheet[`C${row}`].v * sizeMultiplier;
            const yCoord = sheet[`D${row}`].v * sizeMultiplier;

            let elem = $("<area>");
            elem.prop("shape", "circle");
            elem.prop("coords", `${xCoord}, ${yCoord}, ${areaRadius}`);
            elem.prop("id", eventName);
            // DOM elements for Tooltipster
            elem.addClass("tooltip");
            elem.attr("title", eventName);

            imageMap.append(elem);
            row++;
        }
        $(".tooltip").tooltipster();
    } catch (e) {
        console.error(e);
    }
}

main();