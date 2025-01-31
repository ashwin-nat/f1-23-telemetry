class PaceComparison {
    constructor() {
        // Initialize element references
        this.container = document.getElementById('paceComparisonWidget');
        this.prevDriver = document.getElementById('paceComparisonPrev');
        this.nextDriver = document.getElementById('paceComparisonNext');
        this.prevDelta = document.getElementById('paceComparisonPrevDelta');
        this.nextDelta = document.getElementById('paceComparisonNextDelta');

        this.prevSectors = [
            document.getElementById('prevSector1'),
            document.getElementById('prevSector2'),
            document.getElementById('prevSector3')
        ];
        this.nextSectors = [
            document.getElementById('nextSector1'),
            document.getElementById('nextSector2'),
            document.getElementById('nextSector3')
        ];
    }

    #formatDelta(deltaMs) {
        if (!deltaMs && deltaMs !== 0) {
          return '--.-';
        }

        const seconds = Math.abs(deltaMs) / 1000;
        return (deltaMs > 0 ? '+' : '-') + seconds.toFixed(3);
    }

    #updateElementDelta(element, delta) {
        // Remove existing color classes
        element.classList.remove('text-success', 'text-danger');

        // Add appropriate color class based on delta
        if (delta > 0) {
            element.classList.add('text-danger');
        } else if (delta < 0) {
            element.classList.add('text-success');
        }
    }

    #getDriverName(driver) {
        const name = driver['name'];
        if (name === null) {
            return '---';
        } else {
            return truncateName(driver['name']).toUpperCase();
        }
    }

    #clearPrevData() {
        this.prevDelta.textContent = '---';
        this.prevSectors.forEach(el => el.textContent = '---');
    }

    #clearNextData() {
        this.nextDelta.textContent = '---';
        this.nextSectors.forEach(el => el.textContent = '---');
    }

    #isDataAvailable(data) {
        if (data['last-ms'] !== null && data['sector-1-ms'] !== null &&
            data['sector-2-ms'] !== null && data['sector-3-ms'] !== null) {
            return true;
        } else {
            return false;
        }
    }

    /**
     * Updates the UI with new timing data
     * @param {Object} data - The timing data object containing:
     *   - player-last-lap-ms: number
     *   - prev-last-lap-ms: number
     *   - next-last-lap-ms: number
     *   - prev-driver: string
     *   - next-driver: string
     *   - player-sector-1-ms: number
     *   - player-sector-2-ms: number
     *   - player-sector-3-ms: number
     *   - prev-sector1-ms: number
     *   - prev-sector2-ms: number
     *   - prev-sector3-ms: number
     *   - next-sector1-ms: number
     *   - next-sector2-ms: number
     *   - next-sector3-ms: number
     */
    update(data) {
        this.#clearPrevData();
        this.#clearNextData();

        // Fill in the names if available
        if (data['prev']['name'] !== null) {
            this.prevDriver.textContent = this.#getDriverName(data['prev']);
        }
        if (data['next']['name'] !== null) {
            this.nextDriver.textContent = this.#getDriverName(data['next']);
        }

        // If player's data is not available, do nothing
        if (!this.#isDataAvailable(data['player'])) {
            return;
        }

        const isPrevDataAvailable = this.#isDataAvailable(data['prev']);
        const isNextDataAvailable = this.#isDataAvailable(data['next']);

        if (isPrevDataAvailable) {
            const prevDelta = data['player']['lap-ms'] - data['prev']['lap-ms'];
            this.prevDelta.textContent = this.#formatDelta(prevDelta);
            this.#updateElementDelta(this.prevDelta, prevDelta);
        }

        if (isNextDataAvailable) {
            const nextDelta = data['player']['lap-ms'] - data['next']['lap-ms'];
            this.nextDelta.textContent = this.#formatDelta(nextDelta);
            this.#updateElementDelta(this.nextDelta, nextDelta);
        }

        if (!isPrevDataAvailable && !isNextDataAvailable) {
            console.error("Both prev and next data are unavailable", data);
            return;
        }

        // Update sector times and colors
        for (let i = 0; i < 3; i++) {
            if (isPrevDataAvailable) {
                const prevSectorDelta = data['player'][`sector-${i+1}-ms`] - data['prev'][`sector-${i+1}-ms`];
                this.prevSectors[i].textContent = this.#formatDelta(prevSectorDelta);
                this.#updateElementDelta(this.prevSectors[i], prevSectorDelta);
            }
            if (isNextDataAvailable) {
                const nextSectorDelta = data['player'][`sector-${i+1}-ms`] - data['next'][`sector-${i+1}-ms`];
                this.nextSectors[i].textContent = this.#formatDelta(nextSectorDelta);
                this.#updateElementDelta(this.nextSectors[i], nextSectorDelta);
            }
        }
    }
}
