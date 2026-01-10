import streamlit as st
import requests
import pandas as pd
from PIL import Image
import io
import base64
import json
from typing import Dict, List, Any

# Config
API_BASE_URL = "https://tmsearchapi.beyondatagroup.com/"

st.set_page_config(
    page_title="Trademark AI Search Platform",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        background: linear-gradient(120deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        color: #666;
        font-size: 1.1rem;
        margin-bottom: 2rem;
    }
    .result-card {
        border: 1px solid #e0e0e0;
        border-radius: 10px;
        padding: 1rem;
        margin-bottom: 1rem;
        background: white;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        transition: all 0.3s ease;
    }
    .result-card:hover {
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        transform: translateY(-2px);
    }
    .score-badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-weight: 600;
        font-size: 0.9rem;
    }
    .score-high {
        background: #d4edda;
        color: #155724;
    }
    .score-medium {
        background: #fff3cd;
        color: #856404;
    }
    .score-low {
        background: #f8d7da;
        color: #721c24;
    }
    .vienna-badge {
        display: inline-block;
        padding: 0.3rem 0.8rem;
        margin: 0.2rem;
        border-radius: 15px;
        background: #e3f2fd;
        color: #1565c0;
        font-size: 0.85rem;
        font-weight: 500;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 2rem;
    }
    .stTabs [data-baseweb="tab"] {
        height: 3rem;
        padding: 0 2rem;
        font-size: 1rem;
        font-weight: 500;
    }
</style>
""", unsafe_allow_html=True)

# Helper functions
def get_score_class(score: float) -> str:
    """Return CSS class based on score"""
    if score >= 0.7:
        return "score-high"
    elif score >= 0.4:
        return "score-medium"
    else:
        return "score-low"

def display_result_card(result: Dict[str, Any], show_weights: bool = False):
    """Display a single result card with enhanced styling"""
    col1, col2, col3 = st.columns([1, 3, 1])
    
    with col1:
        # Display image
        if 'image_url' in result and result['image_url']:
            try:
                img_response = requests.get(result['image_url'], timeout=10)
                if img_response.status_code == 200:
                    img = Image.open(io.BytesIO(img_response.content))
                    st.image(img, use_container_width=True)
                else:
                    st.info("📷 Image unavailable")
            except:
                st.warning("⚠️ Image load failed")
        else:
            st.info("📷 No image")
    
    with col2:
        # Application details
        app_num = result.get('application_number', 'N/A')
        st.markdown(f"**Application:** `{app_num}`")
        
        if 'verbal_element' in result and result['verbal_element']:
            st.markdown(f"**Brand:** {result['verbal_element']}")
        
        # Metadata
        meta_items = []
        if 'class' in result:
            meta_items.append(f"Class: {result['class']}")
        if 'trade_mark_type' in result:
            meta_items.append(f"Type: {result['trade_mark_type']}")
        if 'tmr_application_status' in result:
            meta_items.append(f"Status: {result['tmr_application_status']}")
        
        if meta_items:
            st.caption(" | ".join(meta_items))
        
        # Dates
        date_items = []
        if 'application_date' in result and result['application_date']:
            date_items.append(f"Applied: {result['application_date']}")
        if 'trade_mark_reg_date' in result and result['trade_mark_reg_date']:
            date_items.append(f"Registered: {result['trade_mark_reg_date']}")
        
        if date_items:
            st.caption(" | ".join(date_items))
    
    with col3:
        # Scores
        if 'final_score' in result:
            score = result['final_score']
            score_class = get_score_class(score)
            st.markdown(f'<div class="score-badge {score_class}">Score: {score:.4f}</div>', 
                       unsafe_allow_html=True)
            
            if show_weights:
                st.caption(f"🎨 Semantic: {result.get('semantic_score_norm', 0):.3f}")
                st.caption(f"📝 Text: {result.get('text_score_norm', 0):.3f}")
        elif 'score' in result:
            score = result['score']
            score_class = get_score_class(score)
            st.markdown(f'<div class="score-badge {score_class}">Score: {score:.4f}</div>', 
                       unsafe_allow_html=True)
        elif 'text_score' in result:
            score = result['text_score']
            score_class = get_score_class(score)
            st.markdown(f'<div class="score-badge {score_class}">Score: {score:.4f}</div>', 
                       unsafe_allow_html=True)
    
    st.divider()

# Header
st.markdown('<h1 class="main-header">🔍 Trademark AI Search Platform</h1>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">Advanced hybrid search powered by CLIP + TF-IDF with Vienna Classification</p>', 
           unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.header("⚙️ Configuration")
    
    st.subheader("Search Parameters")
    top_n = st.slider("Top N Results", 5, 50, 10, help="Number of results to display")
    candidate_pool = st.slider("Candidate Pool", 50, 2000, 200, step=50, 
                               help="Larger pool = more comprehensive but slower")
    
    st.subheader("Search Weights")
    semantic_weight = st.select_slider(
        "Semantic Weight",
        options=[0.0, 0.25, 0.5, 0.75, 1.0],
        value=0.5,
        help="0.0 = Text only, 1.0 = Image only"
    )
    
    st.subheader("Options")
    use_ocr = st.checkbox("Enable OCR", value=True, help="Extract text from images")
    
    st.subheader("Vienna Classification")
    vienna_threshold = st.slider("Confidence Threshold", 0.0, 1.0, 0.2, 0.05,
                                 help="Minimum confidence for Vienna predictions")
    
    st.divider()
    
    # Health check
    if st.button("🩺 Check API Health", use_container_width=True):
        try:
            response = requests.get(f"{API_BASE_URL}/health", timeout=10)
            if response.status_code == 200:
                health = response.json()
                st.success("✅ API Healthy!")
                with st.expander("Details"):
                    st.json(health)
            else:
                st.error("❌ API Unhealthy")
        except:
            st.error("❌ Cannot connect to API")

# Main tabs
tab1, tab2, tab3, tab4 = st.tabs(["🖼️ Image Search", "🤖 Automated Search", "📝 Text Search", "🏛️ Vienna Classification"])

# TAB 1: Image Search
with tab1:
    st.header("Image Search")
    st.markdown("Upload a trademark image to find similar trademarks using hybrid AI search")
    
    uploaded_file = st.file_uploader(
        "Choose an image...", 
        type=['png', 'jpg', 'jpeg'],
        help="Upload a trademark image",
        key="image_search"
    )
    
    if uploaded_file is not None:
        col1, col2 = st.columns([1, 3])
        with col1:
            st.image(uploaded_file, caption="Query Image", use_container_width=True)
        
        with col2:
            st.info(f"""
            **Search Configuration:**
            - Semantic Weight: {semantic_weight} (Image similarity)
            - Text Weight: {1.0 - semantic_weight} (OCR text matching)
            - OCR: {'Enabled' if use_ocr else 'Disabled'}
            - Candidate Pool: {candidate_pool}
            """)
        
        if st.button("🔍 Search Similar Trademarks", type="primary", use_container_width=True):
            with st.spinner("🔄 Searching trademarks..."):
                try:
                    uploaded_file.seek(0)
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
                        
                        # Display search info
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Results Found", len(data['results']))
                        with col2:
                            st.metric("Semantic Weight", f"{data['semantic_weight']:.2f}")
                        with col3:
                            shape_focus = "🎨 Active" if data.get('shape_focus_active') else "📝 Inactive"
                            st.metric("Shape Focus", shape_focus)
                        
                        # OCR results
                        if data.get('ocr_text'):
                            st.success(f"**OCR Extracted:** {data['ocr_text']}")
                            if data.get('cleaned_ocr_text'):
                                st.info(f"**Cleaned Text:** {data['cleaned_ocr_text']}")
                        
                        st.divider()
                        st.subheader("Search Results")
                        
                        # Display results
                        for result in data['results']:
                            display_result_card(result, show_weights=True)
                    
                    else:
                        st.error(f"❌ API Error: {response.status_code}")
                        with st.expander("Error Details"):
                            st.code(response.text)
                        
                except requests.exceptions.RequestException as e:
                    st.error(f"❌ Connection error: {str(e)}")
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")

# TAB 2: Automated Search
with tab2:
    st.header("Automated Multi-Weight Search")
    st.markdown("🚀 Test **all semantic weights** simultaneously using parallel GPU processing")
    
    uploaded_file_auto = st.file_uploader(
        "Choose an image...", 
        type=['png', 'jpg', 'jpeg'],
        help="Upload a trademark image for automated search",
        key="auto_search"
    )
    
    if uploaded_file_auto is not None:
        col1, col2 = st.columns([1, 3])
        with col1:
            st.image(uploaded_file_auto, caption="Query Image", use_container_width=True)
        
        with col2:
            st.info(f"""
            **Automated Search will test:**
            - ✅ All semantic weights: 0.0, 0.25, 0.5, 0.75, 1.0
            - ✅ Parallel GPU processing for maximum speed
            - ✅ Shape-focus preprocessing when applicable
            - ✅ OCR text extraction: {'Enabled' if use_ocr else 'Disabled'}
            - ✅ Results per weight: {top_n}
            """)
        
        if st.button("🤖 Run Automated Search", type="primary", use_container_width=True):
            with st.spinner("🔄 Running automated search across all weights..."):
                try:
                    uploaded_file_auto.seek(0)
                    files = {'file': uploaded_file_auto.getvalue()}
                    params = {
                        'top_n': top_n,
                        'use_ocr': use_ocr,
                        'candidate_pool': candidate_pool
                    }
                    
                    response = requests.post(
                        f"{API_BASE_URL}/search/automated",
                        files=files,
                        params=params,
                        timeout=120
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        
                        # Display search info
                        col1, col2, col3, col4 = st.columns(4)
                        with col1:
                            st.metric("Weights Tested", len(data['weights_searched']))
                        with col2:
                            st.metric("GPUs Used", len(data.get('gpus_used', [])))
                        with col3:
                            st.metric("Candidate Pool", data['candidate_pool'])
                        with col4:
                            st.metric("Results/Weight", data['top_n'])
                        
                        # OCR results
                        if data.get('ocr_text'):
                            st.success(f"**OCR Extracted:** {data['ocr_text']}")
                            if data.get('cleaned_ocr_text'):
                                st.info(f"**Cleaned Text:** {data['cleaned_ocr_text']}")
                        
                        st.divider()
                        
                        # Display results for each weight
                        for weight_result in data['results_by_weight']:
                            sw = weight_result['semantic_weight']
                            tw = weight_result['text_weight']
                            shape_active = weight_result['shape_focus_active']
                            
                            with st.expander(
                                f"📊 Semantic Weight: {sw:.2f} | Text Weight: {tw:.2f} "
                                f"{'🎨 Shape Focus' if shape_active else '📝 Standard'} "
                                f"({len(weight_result['results'])} results)",
                                expanded=(sw == 0.5)
                            ):
                                for result in weight_result['results']:
                                    display_result_card(result, show_weights=True)
                    
                    else:
                        st.error(f"❌ API Error: {response.status_code}")
                        with st.expander("Error Details"):
                            st.code(response.text)
                        
                except requests.exceptions.RequestException as e:
                    st.error(f"❌ Connection error: {str(e)}")
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")

# TAB 3: Text Search
with tab3:
    st.header("Text Search")
    st.markdown("Search trademarks by text using TF-IDF vectorization")
    
    query = st.text_input(
        "Enter trademark text to search",
        placeholder="e.g., Nike swoosh, Apple logo, Coca Cola, etc.",
        help="Enter brand name or description"
    )
    
    if st.button("🔍 Search by Text", type="primary", use_container_width=True) and query.strip():
        with st.spinner("🔄 Searching..."):
            try:
                params = {'query': query.strip(), 'top_n': top_n}
                response = requests.get(
                    f"{API_BASE_URL}/search/text",
                    params=params,
                    timeout=30
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("Results Found", len(data['results']))
                    with col2:
                        st.info(f"**Cleaned Query:** {data.get('cleaned_query', query)}")
                    
                    st.divider()
                    st.subheader("Search Results")
                    
                    for result in data['results']:
                        display_result_card(result)
                
                else:
                    st.error(f"❌ API Error: {response.status_code}")
                    with st.expander("Error Details"):
                        st.code(response.text)
                    
            except requests.exceptions.RequestException as e:
                st.error(f"❌ Connection error: {str(e)}")
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")

# TAB 4: Vienna Classification
with tab4:
    st.header("Vienna Classification Prediction")
    st.markdown("Predict Vienna classification codes using AI vision analysis")
    
    st.info("""
    **About Vienna Classification:**
    The Vienna Classification is an international classification system for the figurative elements of marks.
    It helps categorize visual elements in trademarks (e.g., animals, plants, geometric shapes, etc.)
    """)
    
    uploaded_file_vienna = st.file_uploader(
        "Choose an image...", 
        type=['png', 'jpg', 'jpeg'],
        help="Upload a trademark image for Vienna classification",
        key="vienna_search"
    )
    
    if uploaded_file_vienna is not None:
        col1, col2 = st.columns([1, 2])
        with col1:
            st.image(uploaded_file_vienna, caption="Query Image", use_container_width=True)
        
        with col2:
            st.info(f"""
            **Classification Settings:**
            - Confidence Threshold: {vienna_threshold:.2f}
            - Model: GPT-4 Vision
            - Returns: Category codes, descriptions, types, and probabilities
            """)
        
        if st.button("🏛️ Predict Vienna Classes", type="primary", use_container_width=True):
            with st.spinner("🔄 Analyzing image and predicting Vienna classes..."):
                try:
                    uploaded_file_vienna.seek(0)
                    files = {'image': uploaded_file_vienna.getvalue()}
                    params = {'threshold_probability': vienna_threshold}
                    
                    response = requests.post(
                        f"{API_BASE_URL}/predict/vienna-classes/",
                        files=files,
                        params=params,
                        timeout=60
                    )
                    
                    if response.status_code == 200:
                        predictions = response.json()
                        
                        if predictions:
                            st.success(f"✅ Found {len(predictions)} Vienna classifications")
                            
                            st.divider()
                            st.subheader("Predicted Classifications")
                            
                            # Display as cards
                            for pred in predictions:
                                with st.container():
                                    col1, col2, col3 = st.columns([2, 4, 1])
                                    
                                    with col1:
                                        st.markdown(f"**Code:** `{pred['category_code']}`")
                                        st.caption(f"Type: {pred['category_type']}")
                                    
                                    with col2:
                                        st.markdown(f"**Description:** {pred['description']}")
                                    
                                    with col3:
                                        prob = pred['probability']
                                        score_class = get_score_class(prob)
                                        st.markdown(
                                            f'<div class="score-badge {score_class}">{prob:.1%}</div>', 
                                            unsafe_allow_html=True
                                        )
                                    
                                    st.divider()
                            
                            # Download as JSON
                            st.download_button(
                                label="📥 Download Results (JSON)",
                                data=json.dumps(predictions, indent=2),
                                file_name="vienna_classifications.json",
                                mime="application/json"
                            )
                            
                            # Display as table
                            with st.expander("📊 View as Table"):
                                df = pd.DataFrame(predictions)
                                st.dataframe(df, use_container_width=True)
                        
                        else:
                            st.warning("⚠️ No Vienna classifications found above the threshold")
                    
                    else:
                        st.error(f"❌ API Error: {response.status_code}")
                        with st.expander("Error Details"):
                            st.code(response.text)
                        
                except requests.exceptions.RequestException as e:
                    st.error(f"❌ Connection error: {str(e)}")
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; padding: 2rem 0;'>
    <p><strong>Trademark AI Search Platform</strong> | Powered by CLIP + TF-IDF + GPT-4 Vision</p>
    <p>Advanced hybrid search with Vienna classification support</p>
</div>
""", unsafe_allow_html=True)
