import { clearTable, getTyreIconSpan } from "./utils.js";

export class LapTimeTableWidget {
    constructor() {
        this.lapTimeTable = document.getElementById('lapTimeTable');
    }

    // Method to get the valid time string
    getValidTimeStr(timeMs, timeStr) {
        return timeMs === 0 ? "---" : timeStr;
    }

    // Method to update the lap time table with provided lap history
    update(lapTimeHistory) {
        clearTable(this.lapTimeTable, true); // Clear the table first

        if (lapTimeHistory === null) {
            return;
        }

        const {
            'fastest-lap-number': pbLapNum,
            'fastest-s1-lap-number': pbS1LapNum,
            'fastest-s2-lap-number': pbS2LapNum,
            'fastest-s3-lap-number': pbS3LapNum,
            'global-fastest-lap-ms': globalBestLapMs,
            'global-fastest-s1-ms': globalBestS1Ms,
            'global-fastest-s2-ms': globalBestS2Ms,
            'global-fastest-s3-ms': globalBestS3Ms,
            'lap-time-history-data': lapHistoryData
        } = lapTimeHistory;

        const numRows = 5; // Limit to 5 rows
        let count = 0;

        for (let i = lapHistoryData.length - 1; i >= 0 && count < numRows; i--, count++) {
            const lapData = lapHistoryData[i];
            const lapNumber = i + 1;

            const compound = lapData["tyre-set-info"] !== null ? lapData["tyre-set-info"]["visual-tyre-compound"] : "";
            const lapTimeMs = lapData["lap-time-in-ms"];
            const lapTimeStr = lapData["lap-time-str"];
            const s1TimeMs = lapData["sector-1-time-in-ms"];
            const s1TimeStr = lapData["sector-1-time-str"];
            const s2TimeMs = lapData["sector-2-time-in-ms"];
            const s2TimeStr = lapData["sector-2-time-str"];
            const s3TimeMs = lapData["sector-3-time-in-ms"];
            const s3TimeStr = lapData["sector-3-time-str"];

            const validFlags = lapData["lap-valid-bit-flags"];
            const lapValidMask = 1;
            const s1ValidMask = 2;
            const s2ValidMask = 4;
            const s3ValidMask = 8;

            const row = this.lapTimeTable.insertRow();
            const lapNumCell = row.insertCell();
            const lapTimeCell = row.insertCell();
            const s1TimeCell = row.insertCell();
            const s2TimeCell = row.insertCell();
            const s3TimeCell = row.insertCell();
            const compoundCell = row.insertCell();

            // Append the span to the compoundCell if compound exists
            if (compound) {
                compoundCell.appendChild(getTyreIconSpan(compound));
            }

            lapNumCell.textContent = lapNumber;
            lapTimeCell.textContent = this.getValidTimeStr(lapTimeMs, lapTimeStr);
            s1TimeCell.textContent = this.getValidTimeStr(s1TimeMs, s1TimeStr);
            s2TimeCell.textContent = this.getValidTimeStr(s2TimeMs, s2TimeStr);
            s3TimeCell.textContent = this.getValidTimeStr(s3TimeMs, s3TimeStr);

            this.applyColourToCell(lapTimeCell, lapNumber, lapTimeMs, globalBestLapMs, pbLapNum, (validFlags & lapValidMask), "lap");
            this.applyColourToCell(s1TimeCell, lapNumber, s1TimeMs, globalBestS1Ms, pbS1LapNum, (validFlags & s1ValidMask), "s1");
            this.applyColourToCell(s2TimeCell, lapNumber, s2TimeMs, globalBestS2Ms, pbS2LapNum, (validFlags & s2ValidMask), "s2");
            this.applyColourToCell(s3TimeCell, lapNumber, s3TimeMs, globalBestS3Ms, pbS3LapNum, (validFlags & s3ValidMask), "s3");
        }
    }

    // Method to apply color based on conditions
    applyColourToCell(cell, lapNum, time, globalBestTime, pbLapNum, isValid, typeStr) {
        if (globalBestTime && (time === globalBestTime)) {
            // purple time
            cell.classList.add("text-purple");
        } else if (pbLapNum && (lapNum === pbLapNum)) {
            // green time
            cell.classList.add("text-success");
        } else if (!isValid) {
            // red time
            cell.classList.add("text-danger");
        }
    }
}
