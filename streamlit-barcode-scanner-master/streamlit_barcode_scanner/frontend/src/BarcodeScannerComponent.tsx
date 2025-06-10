import {
  Streamlit,
  StreamlitComponentBase,
  withStreamlitConnection,
} from "streamlit-component-lib"
import React, { ComponentProps, ReactNode, RefObject} from "react"

import { Html5QrcodeScanner, } from 'html5-qrcode';
import { Html5QrcodeError, Html5QrcodeResult, Html5QrcodeSupportedFormats } from "html5-qrcode/esm/core";

const qrcodeRegionId = "html5qr-code-full-region";

class BarcodeScannerComponent extends StreamlitComponentBase {

  private lastDecoded: string | null = null;

  private html5QrcodeScanner: Html5QrcodeScanner | null = null;;

  componentDidMount() {
    super.componentDidMount();
    this.html5QrcodeScanner = new Html5QrcodeScanner(
      qrcodeRegionId, 
      {
        ...this.props.args,
        ...{
          videoConstraints:{height:this.props.args.height},
          formatsToSupport:Object.values(Html5QrcodeSupportedFormats) as any
        }
      }, 
      false
    );
    this.html5QrcodeScanner.render(this.success.bind(this), this.error.bind(this));
    Streamlit.setFrameHeight()
  }

  componentWillUnmount(): void {
    this.html5QrcodeScanner?.clear().catch(error => {
      console.error("Failed to clear html5QrcodeScanner. ", error);
  });
  }

  public render = (): ReactNode => {
    return (
      <div
      id={qrcodeRegionId}
      style={{
        minHeight:'600px'
      }}
      />
    )
  }

  private success(decodedText: string,result:Html5QrcodeResult ) {
    if (decodedText !== this.lastDecoded) {
      Streamlit.setComponentValue(decodedText)
      this.lastDecoded = decodedText
    }
  }

  private error(errorMessage: string, error: Html5QrcodeError) {
    //
  }

}

export default withStreamlitConnection(BarcodeScannerComponent)
