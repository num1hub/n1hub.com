# Example: Uploading a Document

This example walks through uploading a document and verifying it was processed correctly.

## Scenario

You have a research paper about neural networks that you want to add to your knowledge base.

## Step-by-Step Guide

### Step 1: Prepare Your Content

**Title:** "Neural Networks: An Introduction"

**Content:**
\`\`\`
Neural networks are computing systems inspired by biological neural networks.
They consist of interconnected nodes (neurons) organized in layers.

The basic structure includes:
- Input layer: Receives data
- Hidden layers: Process information
- Output layer: Produces results

Training involves adjusting weights through backpropagation to minimize error.
Popular architectures include feedforward networks, CNNs, and RNNs.

Applications span image recognition, natural language processing, and more.
\`\`\`

**Tags:** `neural-networks, machine-learning, ai, deep-learning, algorithms`

### Step 2: Upload via UI

1. Navigate to the home page (`/`)
2. Enter title: "Neural Networks: An Introduction"
3. Paste content into the Material field
4. Enter tags: `neural-networks, machine-learning, ai, deep-learning, algorithms`
5. Ensure "Include in RAG scope" is checked
6. Click "Create Capsule"

### Step 3: Monitor Job Progress

1. Go to `/inbox`
2. Find your job (should show "queued" or "processing")
3. Wait for status to change to "succeeded"
4. Note the capsule ID from the job details

**Expected Timeline:**
- Queued: Immediate
- Processing: 5-15 seconds
- Succeeded: 10-30 seconds total

### Step 4: Verify Capsule

1. Go to `/capsules`
2. Find your capsule by title or capsule ID
3. Click to view details
4. Verify:
   - Summary is 70-140 words
   - Keywords include relevant terms
   - Tags match your input
   - Status is "active"
   - Include in RAG is true

### Step 5: Test with Chat

1. Go to `/chat`
2. Select "My Capsules" scope
3. Ask: "What are neural networks?"
4. Verify answer includes citations
5. Check that your capsule ID appears in sources

## Expected Results

**Capsule Structure:**
- Metadata with proper tags and semantic hash
- Summary covering key concepts
- Keywords: neural networks, machine learning, layers, training, etc.
- Status: active
- Include in RAG: true

**Chat Response:**
- Answer mentions neural networks
- Citations include your capsule ID
- Metrics show good retrieval and faithfulness scores

## Troubleshooting

**Job Stuck:**
- Check job logs for errors
- Verify content isn't too large
- Try with simpler content first

**Capsule Not Found:**
- Check job completed successfully
- Verify filters on capsules page
- Check capsule status is "active"

**Poor Chat Answer:**
- Ensure capsule has `include_in_rag=true`
- Upload more related content
- Try more specific queries

## Next Steps

- Upload related documents to build knowledge base
- Create links between related capsules
- Experiment with different RAG-Scope profiles
- Review and refine tags for better organization
