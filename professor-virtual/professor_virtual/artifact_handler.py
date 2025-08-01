"""Frontend integration guidelines for file uploads in Professor Virtual.

FRONTEND INTEGRATION GUIDELINES
================================

IMPORTANT: The upload functionality has been moved to tools/upload_arquivo/upload_arquivo.py
as an ADK Tool to properly use ToolContext instead of InvocationContext.

This module now serves as documentation for frontend developers on how to integrate
with the Professor Virtual file upload system.

Frontend developers must follow these guidelines for proper integration.

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
    "version": 0,  // Note: version is now an integer, not "v1"
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

HOW IT WORKS NOW
----------------
The file upload functionality is implemented as an ADK Tool called 'upload_arquivo'.
When the frontend sends an upload request, the ADK agent will automatically invoke
this tool, which has access to the proper ToolContext for saving artifacts.

The flow is:
1. Frontend sends JSON request with file data
2. ADK Runner receives the request
3. Agent processes the request and invokes 'upload_arquivo' tool
4. Tool saves the artifact and returns confirmation
5. Response is sent back to frontend

IMPORTANT CHANGES:
- The version field in responses is now an integer (0, 1, 2...) not a string ("v1")
- The actual implementation is in tools/upload_arquivo/upload_arquivo.py
- The tool uses ToolContext which has the save_artifact method

Example Response (note the integer version):
{
    "success": true,
    "filename": "student_question_001.wav",
    "version": 0,  // Integer, not "v1"
    "size": 46382
}