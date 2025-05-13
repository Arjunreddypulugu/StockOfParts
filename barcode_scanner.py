import cv2
from pyzbar.pyzbar import decode
import time
import numpy as np

def scan_barcode():
    """
    Open the camera and scan for barcodes.
    Returns the scanned barcode data or None if cancelled.
    """
    # Initialize the camera
    cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        print("Error: Could not open camera.")
        return None
    
    # Set a timeout for scanning (10 seconds)
    start_time = time.time()
    timeout = 10
    
    while time.time() - start_time < timeout:
        # Read a frame from the camera
        ret, frame = cap.read()
        
        if not ret:
            print("Error: Could not read frame.")
            break
        
        # Find barcodes in the frame
        barcodes = decode(frame)
        
        # Display the frame
        cv2.imshow('Barcode Scanner', frame)
        
        # Process detected barcodes
        for barcode in barcodes:
            # Extract barcode data
            barcode_data = barcode.data.decode('utf-8')
            
            # Draw a rectangle around the barcode
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
            
            # Release resources and return the barcode data
            cap.release()
            cv2.destroyAllWindows()
            return barcode_data
        
        # Check for key press to exit
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    # Release resources if no barcode was found
    cap.release()
    cv2.destroyAllWindows()
    return None 