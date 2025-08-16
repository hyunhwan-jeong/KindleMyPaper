# TypeError: object NoneType can't be used in 'await' expression in EPUB Download

## 🐛 **Bug Description**

When generating and downloading EPUB files, the application crashes with a `TypeError` related to the FileResponse background task.

## 🔍 **Error Details**

**Error Message:**
```
ERROR: Exception in ASGI application
Traceback (most recent call last):
  File "/venv/lib/python3.13/site-packages/uvicorn/protocols/http/h11_impl.py", line 408, in run_asgi
    result = await app(
  ...
  File "/venv/lib/python3.13/site-packages/starlette/responses.py", line 366, in __call__
    await self.background()
TypeError: object NoneType can't be used in 'await' expression
```

## 🔍 **Root Cause**

The issue occurs in the `/api/generate-epub` endpoint where `FileResponse` is used with a lambda function as the background task:

```python
return FileResponse(
    epub_path,
    media_type="application/epub+zip",
    filename=f"{extracted_title}.epub",
    background=lambda: shutil.rmtree(temp_dir)  # ❌ This returns None
)
```

**Problem:** The lambda function `lambda: shutil.rmtree(temp_dir)` returns `None`, but FastAPI's ASGI expects the background task to be awaitable or return an awaitable.

## ✅ **Solution**

Replace the lambda with a proper function:

```python
# Define cleanup function
def cleanup_temp_dir():
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)

# Return the EPUB file
return FileResponse(
    epub_path,
    media_type="application/epub+zip",
    filename=f"{extracted_title}.epub",
    background=cleanup_temp_dir  # ✅ Proper function reference
)
```

## 🧪 **How to Reproduce**

1. Upload a PDF file
2. Convert to markdown 
3. Generate EPUB
4. Observe the error in server logs during download

## 📋 **Impact**

- **Severity:** High - Breaks EPUB download functionality
- **User Experience:** Users cannot download generated EPUB files
- **Server Stability:** Causes ASGI exceptions but doesn't crash the server

## ✅ **Fix Status**

**Fixed in:** Branch `hj/fix_rte`
**Commit:** `4c8ceab - Fix FileResponse background task error`

The fix ensures proper cleanup of temporary directories while maintaining stable EPUB download functionality.

## 🔗 **Related Issues**

This was discovered while fixing the primary tensor stack error in PDF conversion. Both issues have been resolved together.
