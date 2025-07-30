"""Handler para processar uploads e criar artifacts do frontend.

FRONTEND INTEGRATION GUIDELINES
================================

This module handles file uploads from frontend applications (Flutter, React, etc.)
and creates ADK artifacts for processing by the Professor Virtual agent.

IMPORTANT: Frontend developers must follow these guidelines for proper integration.

Frontend Request Format
----------------------
The frontend must send data in the following JSON format:

{
    "action": "upload_file",
    "file_data": {
        "content": "base64_encoded_content",
        "mime_type": "audio/wav",  // or "image/jpeg", "image/png", etc.
        "filename": "pergunta_aluno_123.wav"
    },
    "session_id": "session_abc",
    "user_id": "user_123"
}

Frontend MUST:
- Convert all files to base64 before sending
- Include the correct MIME type for each file
- Provide a unique filename for tracking
- Wait for backend confirmation with filename and version
- Handle error responses appropriately

Frontend MUST NOT:
- Expect the Runner to create artifacts automatically
- Send binary files directly in the request body
- Use ADK APIs directly (there is no official Flutter SDK)
- Assume uploads are successful without confirmation

Supported File Types
-------------------
- Audio: audio/wav, audio/mp3, audio/mpeg, audio/webm
- Images: image/jpeg, image/png, image/gif, image/webp

Response Format
--------------
Success Response:
{
    "success": true,
    "filename": "pergunta_aluno_123.wav",
    "version": "v1",
    "size": 123456
}

Error Response:
{
    "success": false,
    "error": "Description of what went wrong"
}

Example Frontend Code (Flutter)
------------------------------
```dart
// Convert file to base64
String base64Content = base64Encode(await file.readAsBytes());

// Prepare request
Map<String, dynamic> requestData = {
  'action': 'upload_file',
  'file_data': {
    'content': base64Content,
    'mime_type': 'audio/wav',
    'filename': 'question_${DateTime.now().millisecondsSinceEpoch}.wav'
  },
  'session_id': currentSessionId,
  'user_id': currentUserId
};

// Send to backend
final response = await http.post(
  Uri.parse('https://api.example.com/upload'),
  headers: {'Content-Type': 'application/json'},
  body: jsonEncode(requestData),
);

// Handle response
final responseData = jsonDecode(response.body);
if (responseData['success']) {
  print('File uploaded: ${responseData['filename']} v${responseData['version']}');
} else {
  print('Upload failed: ${responseData['error']}');
}
```
"""

import base64
from typing import Dict, Any
from google.genai import types
from google.adk.agents.invocation_context import InvocationContext


async def handle_file_upload(
    file_data: Dict[str, Any],
    context: InvocationContext
) -> Dict[str, Any]:
    """
    Processa upload de arquivo do frontend e cria artifact.
    
    This function is the main entry point for frontend file uploads.
    It handles the conversion from base64 data to ADK artifacts.
    
    Args:
        file_data: Dict containing:
            - content: Base64 encoded file content (string)
            - mime_type: MIME type of the file (e.g., "audio/wav", "image/jpeg")
            - filename: Unique filename for the artifact
        context: ADK InvocationContext for artifact management
        
    Returns:
        Dict containing:
            - success: Boolean indicating if upload was successful
            - filename: The filename used for the artifact (on success)
            - version: The version assigned by ADK (on success)
            - size: Size of the file in bytes (on success)
            - error: Error message (on failure)
            
    Example:
        >>> file_data = {
        ...     "content": "UklGRi4AAABXQVZFZm10IBAAAAABAAEAQB...",
        ...     "mime_type": "audio/wav",
        ...     "filename": "student_question_001.wav"
        ... }
        >>> result = await handle_file_upload(file_data, context)
        >>> print(result)
        {
            "success": True,
            "filename": "student_question_001.wav",
            "version": "v1",
            "size": 46382
        }
    """
    try:
        # Decodificar base64 se necessário
        if isinstance(file_data['content'], str):
            content_bytes = base64.b64decode(file_data['content'])
        else:
            content_bytes = file_data['content']
            
        # Criar Part do arquivo
        artifact = types.Part.from_data(
            data=content_bytes,
            mime_type=file_data['mime_type']
        )
        
        # Salvar artifact
        version = await context.save_artifact(
            filename=file_data['filename'],
            artifact=artifact
        )
        
        return {
            "success": True,
            "filename": file_data['filename'],
            "version": version,
            "size": len(content_bytes)
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }