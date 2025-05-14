import time
import numpy as np
import streamlit as st
import streamlit.components.v1 as components

# Try to import OpenCV and pyzbar
try:
    import cv2
    from pyzbar.pyzbar import decode
    CV_AVAILABLE = True
except ImportError:
    CV_AVAILABLE = False

def html5_qr_scanner(callback_key=None):
    """
    Create an HTML5-based QR/barcode scanner component.
    
    Args:
        callback_key: Optional session state key to store the scanned result
    
    Returns:
        The HTML/JS component for rendering
    """
    return components.html(
        """
        <div style="margin-bottom: 20px;">
            <div id="reader" style="width: 100%;"></div>
            <div id="scanned-result" style="margin-top: 10px; font-weight: bold;"></div>
        </div>

        <script src="https://unpkg.com/html5-qrcode@2.3.8/html5-qrcode.min.js"></script>
        <script>
            // Initialize scanner
            const html5QrCode = new Html5Qrcode("reader");
            const scannedResult = document.getElementById('scanned-result');
            
            // Start scanning
            html5QrCode.start(
                { facingMode: "environment" }, 
                {
                    fps: 10,
                    qrbox: 250
                },
                (decodedText, decodedResult) => {
                    console.log(`Scan result: ${decodedText}`, decodedResult);
                    html5QrCode.stop();
                    
                    // Display the scanned result
                    scannedResult.innerText = `Scanned: ${decodedText}`;
                    
                    // Send the value to Streamlit via window.parent.postMessage
                    const data = {
                        scanned_value: decodedText
                    };
                    
                    // Use timeout to ensure the message is displayed before redirecting
                    setTimeout(() => {
                        // Fill the input field with the scanned value
                        const inputField = document.getElementById('scanned_value_input');
                        if (inputField) {
                            inputField.value = decodedText;
                            // Trigger a change event to update Streamlit's state
                            const event = new Event('input', { bubbles: true });
                            inputField.dispatchEvent(event);
                        }
                        
                        // Auto-click the "Use This Value" button after a short delay
                        setTimeout(() => {
                            const useValueButton = document.querySelector('button[data-testid="baseButton-secondary"]');
                            if (useValueButton) {
                                useValueButton.click();
                            }
                        }, 500);
                    }, 1000);
                },
                (errorMessage) => {
                    console.log(`QR Code scanning error: ${errorMessage}`);
                }
            ).catch((err) => {
                console.log(`Unable to start scanner: ${err}`);
            });
        </script>
        """,
        height=400
    )

def scan_barcode():
    """
    Open the camera and scan for barcodes.
    Returns the scanned barcode data or None if cancelled.
    """
    if not CV_AVAILABLE:
        st.error("OpenCV or pyzbar is not available. Barcode scanning is disabled.")
        # Provide a text input as fallback
        barcode_data = st.text_input("Enter barcode data manually:")
        if barcode_data:
            return barcode_data
        return None
    
    # Check if running in Streamlit Cloud (headless environment)
    try:
        # Initialize the camera
        cap = cv2.VideoCapture(0)
        
        if not cap.isOpened():
            st.error("Could not open camera. Running in headless environment?")
            barcode_data = st.text_input("Enter barcode data manually:")
            if barcode_data:
                return barcode_data
            return None
        
        # Set a timeout for scanning (10 seconds)
        start_time = time.time()
        timeout = 10
        
        while time.time() - start_time < timeout:
            # Read a frame from the camera
            ret, frame = cap.read()
            
            if not ret:
                st.error("Could not read frame.")
                break
            
            # Find barcodes in the frame
            barcodes = decode(frame)
            
            # Display the frame
            try:
                cv2.imshow('Barcode Scanner', frame)
            except:
                # Running in headless environment, can't show window
                pass
            
            # Process detected barcodes
            for barcode in barcodes:
                # Extract barcode data
                barcode_data = barcode.data.decode('utf-8')
                
                # Try to draw a rectangle around the barcode
                try:
                    points = barcode.polygon
                    if len(points) > 4:
                        hull = cv2.convexHull(np.array([point for point in points], dtype=np.float32))
                        hull = np.intp(hull)
                        cv2.polylines(frame, [hull], True, (0, 255, 0), 2)
                    else:
                        pts = np.array([point for point in points], dtype=np.int32)
                        cv2.polylines(frame, [pts], True, (0, 255, 0), 2)
                    
                    # Display the barcode data
                    cv2.putText(frame, barcode_data, (barcode.rect.left, barcode.rect.top - 10),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
                except:
                    # Skip drawing if in headless environment
                    pass
                
                # Release resources and return the barcode data
                try:
                    cap.release()
                    cv2.destroyAllWindows()
                except:
                    pass
                return barcode_data
            
            # Check for key press to exit
            try:
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
            except:
                # Skip key check if in headless environment
                pass
        
        # Release resources if no barcode was found
        try:
            cap.release()
            cv2.destroyAllWindows()
        except:
            pass
        return None
    except Exception as e:
        st.error(f"Error in barcode scanning: {str(e)}")
        barcode_data = st.text_input("Enter barcode data manually:")
        if barcode_data:
            return barcode_data
        return None 