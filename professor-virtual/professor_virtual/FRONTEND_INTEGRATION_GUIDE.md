# Frontend Integration Guide for Professor Virtual

This guide provides comprehensive instructions for frontend developers integrating with the Professor Virtual ADK backend.

## Overview

The Professor Virtual agent uses Google's ADK (Agent Development Kit) to process educational content including audio transcriptions, image analysis, and text-to-speech generation. Frontend applications communicate with the backend through HTTP endpoints exposed by the ADK Runner.

## Critical Requirements

### What Frontend MUST Do:

1. **Base64 Encoding**: All file uploads must be base64 encoded before sending
2. **JSON Format**: All requests must follow the specified JSON structure
3. **Session Management**: Include session_id and user_id in all requests
4. **Error Handling**: Properly handle backend responses and errors
5. **Confirmation Waiting**: Wait for backend confirmation before proceeding

### What Frontend MUST NOT Do:

1. **No Direct Binary**: Never send binary files directly in request body
2. **No ADK APIs**: Do not attempt to use ADK APIs directly (no Flutter SDK exists)
3. **No Assumptions**: Do not assume uploads succeed without confirmation
4. **No Automatic Artifacts**: Do not expect Runner to create artifacts automatically

## Request Format

All frontend requests must follow this JSON structure:

```json
{
  "action": "upload_file",
  "file_data": {
    "content": "base64_encoded_content",
    "mime_type": "audio/wav",
    "filename": "pergunta_aluno_123.wav"
  },
  "session_id": "session_abc",
  "user_id": "user_123"
}
```

### Field Descriptions:

- **action** (required): The action to perform (e.g., "upload_file", "process_audio")
- **file_data** (required for uploads): Object containing file information
  - **content**: Base64 encoded file content
  - **mime_type**: MIME type of the file
  - **filename**: Unique filename for tracking
- **session_id** (required): Unique session identifier
- **user_id** (required): User identifier for tracking

## Supported File Types

### Audio Files:
- `audio/wav` - WAV audio files
- `audio/mp3` - MP3 audio files
- `audio/mpeg` - MPEG audio files
- `audio/webm` - WebM audio files

### Image Files:
- `image/jpeg` - JPEG images
- `image/png` - PNG images
- `image/gif` - GIF images
- `image/webp` - WebP images

## Response Formats

### Success Response:
```json
{
  "success": true,
  "filename": "pergunta_aluno_123.wav",
  "version": "v1",
  "size": 123456
}
```

### Error Response:
```json
{
  "success": false,
  "error": "Detailed error message explaining what went wrong"
}
```

## Implementation Examples

### Flutter Example:

```dart
import 'dart:convert';
import 'dart:io';
import 'package:http/http.dart' as http;

class ProfessorVirtualAPI {
  static const String baseUrl = 'https://api.example.com';
  
  Future<Map<String, dynamic>> uploadFile(
    File file,
    String mimeType,
    String sessionId,
    String userId,
  ) async {
    try {
      // Step 1: Convert file to base64
      final bytes = await file.readAsBytes();
      final base64Content = base64Encode(bytes);
      
      // Step 2: Prepare request data
      final requestData = {
        'action': 'upload_file',
        'file_data': {
          'content': base64Content,
          'mime_type': mimeType,
          'filename': 'upload_${DateTime.now().millisecondsSinceEpoch}.${_getExtension(mimeType)}',
        },
        'session_id': sessionId,
        'user_id': userId,
      };
      
      // Step 3: Send request
      final response = await http.post(
        Uri.parse('$baseUrl/upload'),
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
        },
        body: jsonEncode(requestData),
      );
      
      // Step 4: Handle response
      final responseData = jsonDecode(response.body);
      
      if (response.statusCode == 200 && responseData['success'] == true) {
        print('File uploaded successfully: ${responseData['filename']} v${responseData['version']}');
        return responseData;
      } else {
        throw Exception(responseData['error'] ?? 'Upload failed');
      }
    } catch (e) {
      print('Error uploading file: $e');
      return {
        'success': false,
        'error': e.toString(),
      };
    }
  }
  
  String _getExtension(String mimeType) {
    final extensions = {
      'audio/wav': 'wav',
      'audio/mp3': 'mp3',
      'audio/mpeg': 'mpeg',
      'audio/webm': 'webm',
      'image/jpeg': 'jpg',
      'image/png': 'png',
      'image/gif': 'gif',
      'image/webp': 'webp',
    };
    return extensions[mimeType] ?? 'bin';
  }
}
```

### React/JavaScript Example:

```javascript
class ProfessorVirtualAPI {
  constructor(baseUrl) {
    this.baseUrl = baseUrl;
  }
  
  async uploadFile(file, sessionId, userId) {
    try {
      // Step 1: Convert file to base64
      const base64Content = await this.fileToBase64(file);
      
      // Step 2: Prepare request data
      const requestData = {
        action: 'upload_file',
        file_data: {
          content: base64Content,
          mime_type: file.type,
          filename: `upload_${Date.now()}_${file.name}`
        },
        session_id: sessionId,
        user_id: userId
      };
      
      // Step 3: Send request
      const response = await fetch(`${this.baseUrl}/upload`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json'
        },
        body: JSON.stringify(requestData)
      });
      
      // Step 4: Handle response
      const responseData = await response.json();
      
      if (response.ok && responseData.success) {
        console.log(`File uploaded: ${responseData.filename} v${responseData.version}`);
        return responseData;
      } else {
        throw new Error(responseData.error || 'Upload failed');
      }
    } catch (error) {
      console.error('Error uploading file:', error);
      return {
        success: false,
        error: error.message
      };
    }
  }
  
  fileToBase64(file) {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.readAsDataURL(file);
      reader.onload = () => {
        // Remove data URL prefix to get pure base64
        const base64 = reader.result.split(',')[1];
        resolve(base64);
      };
      reader.onerror = error => reject(error);
    });
  }
}
```

## API Endpoints

The ADK Runner exposes the following endpoints:

- **POST /invoke** - Main endpoint for agent invocation
- **POST /upload** - File upload endpoint (handled by artifact_handler)
- **GET /session/{session_id}** - Get session status

## Error Handling Best Practices

1. **Network Errors**: Implement retry logic with exponential backoff
2. **Validation Errors**: Display clear messages to users
3. **Size Limits**: Check file size before upload (recommended max: 10MB)
4. **Timeout Handling**: Set appropriate timeouts for large files
5. **Progress Indication**: Show upload progress for better UX

## Testing Recommendations

1. Test with various file sizes and types
2. Test error scenarios (network failures, invalid files)
3. Verify base64 encoding/decoding
4. Test session management across multiple requests
5. Validate MIME type detection

## Security Considerations

1. Validate file types on frontend before upload
2. Implement file size limits
3. Use HTTPS for all communications
4. Sanitize filenames to prevent injection attacks
5. Implement proper authentication and authorization

## Common Issues and Solutions

### Issue: "Upload failed: Invalid base64 content"
**Solution**: Ensure proper base64 encoding without data URL prefix

### Issue: "Session not found"
**Solution**: Create new session or verify session_id is being sent

### Issue: "Unsupported file type"
**Solution**: Check supported MIME types list above

### Issue: Large files failing
**Solution**: Implement chunked upload or increase server timeout

## Additional Resources

- ADK Documentation: [Google ADK Docs](https://developers.google.com/assistant/adk)
- Base64 Encoding: [MDN Base64 Documentation](https://developer.mozilla.org/en-US/docs/Web/API/btoa)
- MIME Types: [IANA Media Types](https://www.iana.org/assignments/media-types/media-types.xhtml)

---

For questions or issues, refer to the artifact_handler.py and agent.py files in the professor_virtual module.