import os
import platform
import sys

import cv2
from insightface.app import FaceAnalysis


def _torch_cuda_dlls_on_path():
    """Expose torch's bundled CUDA/cuDNN DLLs to the process so onnxruntime-gpu
    can (potentially) satisfy its CUDA provider deps on Windows."""
    if platform.system() != "Windows":
        return
    sp = os.path.join(sys.prefix, "Lib", "site-packages")
    torch_lib = os.path.join(sp, "torch", "lib")
    if not os.path.isdir(torch_lib):
        return
    try:
        os.add_dll_directory(torch_lib)
    except Exception:
        pass
    os.environ["PATH"] = torch_lib + os.pathsep + os.environ.get("PATH", "")


def _cuda_provider_usable():
    """onnnxruntime advertises CUDAExecutionProvider even when its CUDA DLL can't
    load, which then logs scary errors and silently falls back. Probe the DLL for real."""
    if platform.system() != "Windows":
        return True
    try:
        import ctypes
        import onnxruntime as ort
        capi = os.path.join(os.path.dirname(ort.__file__), "capi", "onnxruntime_providers_cuda.dll")
        ctypes.WinDLL(capi)
        return True
    except Exception:
        return False


class FaceAnalysisEngine:
    def __init__(self, use_gpu=True):
        _torch_cuda_dlls_on_path()

        requested = ["CPUExecutionProvider"]
        if use_gpu and _cuda_provider_usable():
            requested = ["CUDAExecutionProvider", "CPUExecutionProvider"]

        self.app = FaceAnalysis(name="buffalo_l", providers=requested)
        ctx = 0 if requested[0].startswith("CUDA") else -1
        self.app.prepare(ctx_id=ctx, det_size=(640, 640))

        try:
            applied = self.app.models["recognition"].session.get_providers()
        except Exception:
            applied = []
        self.providers = list(applied)
        self.on_gpu = "CUDAExecutionProvider" in applied
        if self.on_gpu:
            print("FaceEngine: running on GPU (CUDA).")
        else:
            print("FaceEngine: running on CPU.")

    def extract_embeddings(self, img):
        if img is None:
            raise ValueError("uhh image not found? try again girlie")
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        faces = self.app.get(img)
        if not faces:
            return []
        embeddings = []
        for face in faces:
            embeddings.append(face.embedding.tolist())
        return embeddings