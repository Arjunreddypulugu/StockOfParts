import os
import streamlit.components.v1 as components


_RELEASE = True

if not _RELEASE:
    _component_func = components.declare_component(
        "my_component",
        url="http://localhost:3001",
    )
else:
    parent_dir = os.path.dirname(os.path.abspath(__file__))
    build_dir = os.path.join(parent_dir, "frontend/build")
    _component_func = components.declare_component("my_component", path=build_dir)



def qr_scanner(height=600,fps=24,qrbox=250,key=None,**kwargs,):
    component_value = _component_func(key=key,height=height,fps=fps,qrbox=qrbox,**kwargs)
    return component_value
