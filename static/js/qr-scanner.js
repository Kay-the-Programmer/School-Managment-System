/**
 * QR Code Scanner for Attendance Tracking
 * 
 * This script handles the camera access and QR code scanning functionality
 * for the attendance tracking feature.
 */

class QRScanner {
    constructor(videoElement, canvasElement, scanCallback) {
        this.video = videoElement;
        this.canvas = canvasElement;
        this.ctx = this.canvas.getContext('2d');
        this.scanCallback = scanCallback;
        this.isScanning = false;
        this.lastResult = null;
        this.lastResultTime = 0;
    }

    /**
     * Start the QR code scanner
     */
    async start() {
        try {
            // Request camera access
            const stream = await navigator.mediaDevices.getUserMedia({ 
                video: { facingMode: "environment" } 
            });
            
            this.video.srcObject = stream;
            this.video.setAttribute('playsinline', true); // Required for iOS
            this.video.play();
            
            // Start scanning
            this.isScanning = true;
            requestAnimationFrame(() => this.scan());
            
            return true;
        } catch (error) {
            console.error('Error starting QR scanner:', error);
            return false;
        }
    }

    /**
     * Stop the QR code scanner
     */
    stop() {
        this.isScanning = false;
        if (this.video.srcObject) {
            const tracks = this.video.srcObject.getTracks();
            tracks.forEach(track => track.stop());
            this.video.srcObject = null;
        }
    }

    /**
     * Scan for QR codes
     */
    scan() {
        if (!this.isScanning) return;

        if (this.video.readyState === this.video.HAVE_ENOUGH_DATA) {
            // Draw video frame to canvas
            this.canvas.width = this.video.videoWidth;
            this.canvas.height = this.video.videoHeight;
            this.ctx.drawImage(this.video, 0, 0, this.canvas.width, this.canvas.height);
            
            // Get image data for QR code detection
            const imageData = this.ctx.getImageData(0, 0, this.canvas.width, this.canvas.height);
            
            try {
                // Use jsQR library to detect QR code
                // Note: jsQR library must be included in the HTML
                const code = jsQR(imageData.data, imageData.width, imageData.height, {
                    inversionAttempts: "dontInvert",
                });
                
                if (code) {
                    // Prevent duplicate scans (wait 2 seconds between scans)
                    const now = new Date().getTime();
                    if (code.data !== this.lastResult || now - this.lastResultTime > 2000) {
                        this.lastResult = code.data;
                        this.lastResultTime = now;
                        
                        // Draw box around QR code
                        this.drawBox(code.location);
                        
                        // Call callback with QR code data
                        this.scanCallback(code.data);
                    }
                }
            } catch (error) {
                console.error('Error scanning QR code:', error);
            }
        }
        
        // Continue scanning
        requestAnimationFrame(() => this.scan());
    }

    /**
     * Draw a box around the detected QR code
     */
    drawBox(location) {
        this.ctx.beginPath();
        this.ctx.moveTo(location.topLeftCorner.x, location.topLeftCorner.y);
        this.ctx.lineTo(location.topRightCorner.x, location.topRightCorner.y);
        this.ctx.lineTo(location.bottomRightCorner.x, location.bottomRightCorner.y);
        this.ctx.lineTo(location.bottomLeftCorner.x, location.bottomLeftCorner.y);
        this.ctx.lineTo(location.topLeftCorner.x, location.topLeftCorner.y);
        this.ctx.lineWidth = 4;
        this.ctx.strokeStyle = "#FF3B58";
        this.ctx.stroke();
    }
}

// Example usage:
/*
document.addEventListener('DOMContentLoaded', () => {
    const video = document.getElementById('qr-video');
    const canvas = document.getElementById('qr-canvas');
    
    // Create QR scanner
    const scanner = new QRScanner(video, canvas, (result) => {
        console.log('QR Code detected:', result);
        
        // Send result to server
        fetch('/attendance/record/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
            },
            body: JSON.stringify({ uuid: result })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert(`Attendance recorded for ${data.pupil_name}`);
            } else {
                alert(`Error: ${data.error}`);
            }
        })
        .catch(error => {
            console.error('Error recording attendance:', error);
            alert('Error recording attendance. Please try again.');
        });
    });
    
    // Start scanner when button is clicked
    document.getElementById('start-scan').addEventListener('click', () => {
        scanner.start();
    });
    
    // Stop scanner when button is clicked
    document.getElementById('stop-scan').addEventListener('click', () => {
        scanner.stop();
    });
});
*/