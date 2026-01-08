import streamlit as st
import requests
import pandas as pd
from PIL import Image
import io
import base64

# Config
API_BASE_URL = "https://tmsearchapi.beyondatagroup.com/"

st.set_page_config(
    page_title="Trademark Hybrid Search Tester",
    page_icon="🔍",
    layout="wide"
)

st.title("🔍 Trademark Hybrid Search V2 Tester")
st.markdown("Upload an image or enter text to search trademarks using CLIP + TF-IDF")

# Sidebar for settings
st.sidebar.header("⚙️ Search Settings")
semantic_weight = st.sidebar.slider(
    "Semantic Weight (Image Similarity)",
    0.0, 1.0, 0.5, 0.25,
    help="0.0 = Text only, 1.0 = Image only"
)
top_n = st.sidebar.slider("Top N Results", 5, 50, 10)
use_ocr = st.sidebar.checkbox("Use OCR (for image search)", value=True)
candidate_pool = st.sidebar.slider("Candidate Pool", 50, 2000, 200)

# Tabs
tab1, tab2 = st.tabs(["🖼️ Image Search", "📝 Text Search"])

with tab1:
    st.header("Image Search")
    
    uploaded_file = st.file_uploader(
        "Choose an image...", 
        type=['png', 'jpg', 'jpeg'],
        help="Upload a trademark image to search similar ones"
    )
    
    if uploaded_file is not None:
        # Display uploaded image
        col1, col2 = st.columns([1, 3])
        with col1:
            st.image(uploaded_file, caption="Query Image", use_column_width=True)
        
        if st.button("🔍 Search Similar Trademarks", type="primary"):
            with st.spinner("Searching..."):
                try:
                    files = {'file': uploaded_file.getvalue()}
                    params = {
                        'top_n': top_n,
                        'semantic_weight': semantic_weight,
                        'use_ocr': use_ocr,
                        'candidate_pool': candidate_pool
                    }
                    
                    response = requests.post(
                        f"{API_BASE_URL}/search/image",
                        files=files,
                        params=params,
                        timeout=60
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        st.success(f"Found {len(data['results'])} results!")
                        
                        # Display OCR result if available
                        if data.get('ocr_text'):
                            st.info(f"**OCR Text:** {data['ocr_text']}")
                            if data.get('cleaned_ocr_text'):
                                st.info(f"**Cleaned:** {data['cleaned_ocr_text']}")
                        
                        # Results cards
                        for i, result in enumerate(data['results']):
                            with st.container():
                                col1, col2, col3 = st.columns([1, 3, 1])
                                
                                with col1:
                                    score = result.get('final_score', 0)
                                    st.metric("Score", f"{score:.4f}")
                                
                                with col2:
                                    st.markdown(f"**{result.get('application_number', 'N/A')}**")
                                    if 'verbal_element' in result:
                                        st.caption(result['verbal_element'])
                                    st.caption(f"Class: {result.get('class', 'N/A')}")
                                    status = result.get('tmr_application_status', '')
                                    if status:
                                        st.caption(f"Status: {status}")
                                
                                with col3:
                                    if 'image_url' in result and result['image_url']:
                                        try:
                                            img_response = requests.get(result['image_url'], timeout=10)
                                            if img_response.status_code == 200:
                                                img = Image.open(io.BytesIO(img_response.content))
                                                st.image(img, use_column_width=True)
                                            else:
                                                st.error("Image not available")
                                        except:
                                            st.caption("Image load failed")
                                
                                st.divider()
                    
                    else:
                        st.error(f"API Error: {response.status_code} - {response.text}")
                        
                except requests.exceptions.RequestException as e:
                    st.error(f"Connection error: {str(e)}")
                except Exception as e:
                    st.error(f"Error: {str(e)}")

with tab2:
    st.header("Text Search")
    
    query = st.text_input(
        "Enter trademark text to search",
        placeholder="e.g., Nike swoosh, Apple logo, etc."
    )
    
    if st.button("🔍 Search by Text", type="primary") and query.strip():
        with st.spinner("Searching..."):
            try:
                params = {'query': query.strip(), 'top_n': top_n}
                response = requests.get(
                    f"{API_BASE_URL}/search/text",
                    params=params,
                    timeout=30
                )
                
                if response.status_code == 200:
                    data = response.json()
                    st.success(f"Found {len(data['results'])} results!")
                    st.info(f"**Cleaned Query:** {data.get('cleaned_query', query)}")
                    
                    # Results cards
                    for i, result in enumerate(data['results']):
                        with st.container():
                            col1, col2, col3 = st.columns([1, 3, 1])
                            
                            with col1:
                                score = result.get('text_score', 0)
                                st.metric("Score", f"{score:.4f}")
                            
                            with col2:
                                st.markdown(f"**{result.get('application_number', 'N/A')}**")
                                if 'verbal_element' in result:
                                    st.caption(result['verbal_element'])
                                st.caption(f"Class: {result.get('class', 'N/A')}")
                            
                            with col3:
                                if 'image_url' in result and result['image_url']:
                                    try:
                                        img_response = requests.get(result['image_url'], timeout=10)
                                        if img_response.status_code == 200:
                                            img = Image.open(io.BytesIO(img_response.content))
                                            st.image(img, use_column_width=True)
                                        else:
                                            st.caption("Image not available")
                                    except:
                                        st.caption("Image load failed")
                            
                            st.divider()
                
                else:
                    st.error(f"API Error: {response.status_code} - {response.text}")
                    
            except requests.exceptions.RequestException as e:
                st.error(f"Connection error: {str(e)}")
            except Exception as e:
                st.error(f"Error: {str(e)}")

# Health check
if st.sidebar.button("🩺 Check API Health"):
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=10)
        if response.status_code == 200:
            health = response.json()
            st.sidebar.success("✅ API Healthy!")
            st.sidebar.json(health)
        else:
            st.sidebar.error("❌ API Unhealthy")
    except:
        st.sidebar.error("❌ Cannot connect to API")

# Footer
st.markdown("---")
