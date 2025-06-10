import streamlit as st
import streamlit.components.v1 as components

def html5_qr_scanner():
    """
    Create an HTML5-based QR/barcode scanner component.
    
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
            const html5QrCode = new Html5Qrcode("reader");
            const scannedResult = document.getElementById('scanned-result');
            function handleScan(decodedText) {
                if (scannedResult) {
                    scannedResult.innerText = `Scanned: ${decodedText}`;
                }
                if (window.parent && window.parent.postMessage) {
                    window.parent.postMessage({type: 'streamlit:setComponentValue', value: decodedText}, '*');
                }
            }
            html5QrCode.start(
                { facingMode: "environment" },
                {
                    fps: 10,
                    qrbox: 250
                },
                (decodedText, decodedResult) => {
                    html5QrCode.stop();
                    handleScan(decodedText);
                },
                (errorMessage) => {
                    // ignore errors
                }
            ).catch((err) => {
                // ignore errors
            });
        </script>
        """,
        height=400,
        key="html5_qr_scanner",
        default=None
    )

def scan_barcode():
    """
    Open the camera and scan for barcodes.
    Returns the scanned barcode data or None if cancelled.
    """
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