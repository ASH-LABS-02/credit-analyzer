# Intelli-Credit Platform Architecture

## Overview

The Intelli-Credit platform uses a simplified Firebase architecture with only two Firebase services:
- **Firestore**: NoSQL database for all application data
- **Firebase Authentication**: User authentication and authorization

## Architecture Decision: Firestore-Only Storage

### Why No Firebase Storage?

We've chosen to store all data, including documents, directly in Firestore rather than using Firebase Storage for the following reasons:

1. **Simplified Architecture**: Single data store reduces complexity
2. **Atomic Transactions**: All data in one place enables better transaction support
3. **Easier Querying**: Document metadata and content together simplify queries
4. **Cost Efficiency**: For moderate file sizes, Firestore is cost-effective
5. **Reduced Latency**: No need for separate storage service calls

### Document Storage Strategy

Documents are stored in Firestore using base64 encoding:

```javascript
{
  "id": "doc-123",
  "application_id": "app-456",
  "filename": "financial_statement.pdf",
  "file_type": "application/pdf",
  "content_base64": "JVBERi0xLjQKJeLjz9MK...",  // Base64-encoded content
  "file_size": 245678,
  "upload_date": "2024-01-15T10:30:00Z",
  "processing_status": "completed",
  "extracted_data": { ... }
}
```

### Size Limitations

Firestore document size limit: **1 MB**

For documents larger than 1 MB, we use chunking:
- Split document into multiple chunks
- Store each chunk as a separate document
- Link chunks together with parent document reference

```javascript
// Parent document
{
  "id": "doc-123",
  "filename": "large_file.pdf",
  "total_chunks": 5,
  "total_size": 4500000,
  "chunk_ids": ["chunk-1", "chunk-2", "chunk-3", "chunk-4", "chunk-5"]
}

// Chunk documents
{
  "id": "chunk-1",
  "parent_doc_id": "doc-123",
  "chunk_index": 0,
  "content_base64": "...",
  "chunk_size": 900000
}
```

## Data Model

### Firestore Collections

```
/applications/{application_id}
  - company_name: string
  - loan_amount: number
  - status: string
  - created_at: timestamp
  - updated_at: timestamp
  - credit_score: number (optional)
  - recommendation: string (optional)

/applications/{application_id}/documents/{document_id}
  - filename: string
  - file_type: string
  - content_base64: string
  - file_size: number
  - upload_date: timestamp
  - processing_status: string
  - extracted_data: map (optional)

/applications/{application_id}/analysis_results
  - financial_metrics: map
  - forecasts: map
  - risk_score: map
  - research_summary: string
  - generated_at: timestamp

/applications/{application_id}/cam
  - content: string
  - sections: map
  - generated_at: timestamp
  - version: number

/users/{user_id}
  - email: string
  - role: string
  - created_at: timestamp
  - last_login: timestamp

/monitoring/{application_id}
  - monitoring_active: boolean
  - last_check: timestamp
  - alerts: array

/audit_logs/{log_id}
  - user_id: string
  - action: string
  - resource_type: string
  - resource_id: string
  - timestamp: timestamp
  - details: map
```

## Firebase Authentication

### Authentication Flow

1. **User Login**
   ```javascript
   const userCredential = await signInWithEmailAndPassword(auth, email, password);
   const idToken = await userCredential.user.getIdToken();
   ```

2. **Token Verification (Backend)**
   ```python
   from firebase_admin import auth
   
   decoded_token = auth.verify_id_token(id_token)
   uid = decoded_token['uid']
   ```

3. **Role-Based Access Control**
   - Roles stored in Firestore `/users/{uid}` collection
   - Custom claims can be added to tokens for faster access control
   - Middleware validates tokens and checks permissions

### Security Rules

Firestore security rules enforce access control:

```javascript
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    // Applications - authenticated users only
    match /applications/{applicationId} {
      allow read: if request.auth != null;
      allow create: if request.auth != null;
      allow update: if request.auth != null && 
                      get(/databases/$(database)/documents/users/$(request.auth.uid)).data.role in ['analyst', 'admin'];
      allow delete: if request.auth != null && 
                      get(/databases/$(database)/documents/users/$(request.auth.uid)).data.role == 'admin';
      
      // Documents subcollection
      match /documents/{documentId} {
        allow read: if request.auth != null;
        allow write: if request.auth != null;
      }
    }
    
    // Users - own profile only
    match /users/{userId} {
      allow read: if request.auth != null && request.auth.uid == userId;
      allow write: if request.auth != null && request.auth.uid == userId;
    }
    
    // Audit logs - read-only for admins
    match /audit_logs/{logId} {
      allow read: if request.auth != null && 
                    get(/databases/$(database)/documents/users/$(request.auth.uid)).data.role == 'admin';
      allow write: if false; // Only server can write
    }
  }
}
```

## API Integration

### Document Upload Flow

1. **Client uploads file**
   ```javascript
   const formData = new FormData();
   formData.append('file', file);
   formData.append('document_type', 'financial_statement');
   
   const response = await axios.post(
     `/api/v1/applications/${appId}/documents`,
     formData,
     { headers: { 'Authorization': `Bearer ${token}` } }
   );
   ```

2. **Backend processes upload**
   ```python
   # Read file content
   content = await file.read()
   
   # Encode to base64
   base64_content = base64.b64encode(content).decode('utf-8')
   
   # Store in Firestore
   doc_ref = db.collection('applications').document(app_id).collection('documents').document()
   doc_ref.set({
       'filename': file.filename,
       'file_type': file.content_type,
       'content_base64': base64_content,
       'file_size': len(content),
       'upload_date': datetime.utcnow(),
       'processing_status': 'pending'
   })
   ```

3. **Document retrieval**
   ```python
   # Get document from Firestore
   doc = db.collection('applications').document(app_id).collection('documents').document(doc_id).get()
   
   # Decode base64 content
   content = base64.b64decode(doc.get('content_base64'))
   
   # Return file
   return Response(content=content, media_type=doc.get('file_type'))
   ```

## Performance Considerations

### Optimization Strategies

1. **Lazy Loading**: Load document content only when needed
2. **Caching**: Cache frequently accessed documents
3. **Compression**: Compress documents before base64 encoding
4. **Pagination**: Paginate document lists
5. **Indexes**: Create composite indexes for common queries

### Firestore Limits

- **Document size**: 1 MB (use chunking for larger files)
- **Write rate**: 1 write per second per document
- **Read rate**: No limit
- **Collection size**: Unlimited
- **Subcollections**: Unlimited depth

## Deployment

### Environment Variables

```bash
# Firebase Configuration
FIREBASE_PROJECT_ID=your-project-id
FIREBASE_PRIVATE_KEY=your-private-key
FIREBASE_CLIENT_EMAIL=your-client-email

# Application Configuration
API_BASE_URL=http://localhost:8000
FRONTEND_URL=http://localhost:5173

# OpenAI Configuration (for AI agents)
OPENAI_API_KEY=your-openai-key
```

### Firebase Setup

1. **Create Firebase Project**
   - Go to Firebase Console
   - Create new project
   - Enable Firestore
   - Enable Authentication (Email/Password)

2. **Generate Service Account Key**
   - Project Settings → Service Accounts
   - Generate new private key
   - Download JSON file
   - Add credentials to environment variables

3. **Configure Firestore**
   - Create database in production mode
   - Set up security rules
   - Create indexes for queries

4. **Configure Authentication**
   - Enable Email/Password provider
   - Set up authorized domains
   - Configure password policies

## Migration from Firebase Storage

If you previously used Firebase Storage, here's how to migrate:

1. **Download all files from Storage**
2. **Convert to base64 and upload to Firestore**
3. **Update document references**
4. **Test thoroughly**
5. **Delete Storage bucket**

```python
# Migration script example
async def migrate_storage_to_firestore():
    # Get all documents from Storage
    bucket = storage.bucket()
    blobs = bucket.list_blobs()
    
    for blob in blobs:
        # Download file
        content = blob.download_as_bytes()
        
        # Encode to base64
        base64_content = base64.b64encode(content).decode('utf-8')
        
        # Store in Firestore
        doc_ref = db.collection('documents').document(blob.name)
        doc_ref.set({
            'content_base64': base64_content,
            'filename': blob.name,
            'file_size': len(content),
            'migrated_at': datetime.utcnow()
        })
        
        print(f"Migrated: {blob.name}")
```

## Benefits of This Architecture

1. **Simplicity**: Single database service
2. **Consistency**: All data in one place
3. **Transactions**: Atomic operations across all data
4. **Cost**: Predictable pricing
5. **Scalability**: Firestore scales automatically
6. **Security**: Unified security rules
7. **Offline Support**: Firestore offline persistence
8. **Real-time**: Real-time updates for all data

## Trade-offs

1. **File Size Limit**: 1 MB per document (mitigated with chunking)
2. **Base64 Overhead**: ~33% size increase (mitigated with compression)
3. **Query Performance**: Large documents may slow queries (mitigated with lazy loading)

## Conclusion

The Firestore-only architecture provides a simple, scalable, and cost-effective solution for the Intelli-Credit platform. By storing documents as base64-encoded content in Firestore, we eliminate the need for Firebase Storage while maintaining all required functionality.
