import streamlit as st
from PIL import Image
from streamlit_geolocation import streamlit_geolocation
import logic
import pandas as pd
import json
import re
import database



# -----------------------------------------------------------------------------
# 1. PAGE CONFIGURATION
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="MediGrid AI ",
    page_icon="✚",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        #'Get Help' : 'chinnurajula3894@gmail.com',
        'Report a bug' : 'mailto:chinnurajula3894@gmail.com?subject=MediGrid%20Bug',
        'About' : '# MediGrid AI \n Tablets Prescription Analyzer\n Which anlayzes the\
            handwritten tablet prescriptions\n ### created by : Ravindhar'
    }

)
# -----------------------------------------------------------------------------
# 2. VISUAL STYLING (CSS) - LIGHT THEME CONSISTENT
# -----------------------------------------------------------------------------
st.markdown("""
<style>
    html, body, .stApp { font-family: 'Inter', sans-serif; color: #2C3E50; }
    .stApp { background-color: #F0F2F6; }
    [data-testid="stSidebar"] { background-color: #FFFFFF; border-right: 1px solid #E0E0E0; padding-top: 20px; }
    [data-testid="stSidebarHeader"] { padding-top: 0; margin-top: 0; height: auto; }
    h1, h2, h3 { color: #2C3E50; font-weight: 600; }
    .stFileUploader { background-color: #FFFFFF; border: 2px dashed #00A8CC; border-radius: 15px; padding: 20px; }
    .stButton>button { background-color: #00A8CC; color: white; border-radius: 8px; border: none; font-weight: bold; width: 100%; }
    .stButton>button:hover { background-color: #008CA8; color: white; }
    .stTabs [data-baseweb="tab-list"] button[aria-selected="true"] { border-bottom: 2px solid #00A8CC; color: #00A8CC; font-weight: bold; }
</style>
""", unsafe_allow_html=True)
#----------------------------------------------
# AI Assistant Integration (Done with Botpress AI Agent.)
#------------------------------------------------------------------------------

# -----------------------------------------------------------------------------
# 3. SIDEBAR
# -----------------------------------------------------------------------------
with st.sidebar:
    st.markdown("<div style='text-align: center; padding-bottom: 20px;'><h1 style='font-size: 30px;'>✚ MediGrid AI</h1></div>", unsafe_allow_html=True)
    
    st.markdown("### 📍 Location Service")
    st.info("Click below to find nearby pharmacies.")
    location_data = streamlit_geolocation()

    st.markdown("---")
    st.markdown("### 📘 User Guide")
    st.info("1. Upload a prescription.\n2. AI extracts meds & dosage.\n3. Get map links for pharmacies.")
    
    st.markdown("### ⚙️ Settings")
    confidence = st.slider("Confidence Threshold", 50, 100, 85)
    st.caption("🔒 Privacy Note: Data processed locally.")

# -----------------------------------------------------------------------------
# 4. MAIN CONTENT
# -----------------------------------------------------------------------------
st.markdown("<div style='text-align: center; padding-bottom: 20px;'><h1 style='font-size: 50px;'>✚ MediGrid AI</h1></div>", unsafe_allow_html=True)
#st.title("💊 Tablets Prescription Analyzer")
st.markdown("<div style='text-align: left; padding-bottom: 6px;'><h1 style='font-size: 30px;'>💊 Tablets Prescription Analyzer</h1></div>", unsafe_allow_html=True)
st.write("Transform handwritten tablets prescriptions into digital medical insights.")
st.markdown("<br>", unsafe_allow_html=True)

# File Uploader
uploaded_file = st.file_uploader("Drag and drop file here", type=['png', 'jpg', 'jpeg', 'pdf', 'webp'])

u1=st.columns(1)[0]
with u1:
    @st.dialog('📂 All Patient Records',width='large')
    def view_history():
        dff=database.display_table()
        st.dataframe(dff,use_container_width=True,hide_index=True)
    if st.button('View History',use_container_width=True,type='primary'):
        view_history()


# -----------------------------------------------------------------------------
# 5. LOGIC INTEGRATION
# -----------------------------------------------------------------------------
if uploaded_file is not None :
    st.markdown("---")

    file_key = f"{uploaded_file.name}-{uploaded_file.size}" # Create a unique ID for the file
    
    if "last_uploaded_key" not in st.session_state:
        st.session_state.last_uploaded_key = None
        
    if st.session_state.last_uploaded_key != file_key:
        # if New file is detected! then reset the result variable
        st.session_state.analysis_result = ""
        st.session_state.last_uploaded_key = file_key

    col_img, col_data = st.columns([1, 1.5], gap="large")
    
    # LEFT COLUMN: IMAGE
    with col_img:
        st.markdown("### 📄 Uploaded Document")
        image = Image.open(uploaded_file)
        
        
        st.image(image, caption="Source Image", use_container_width=True)

    # RIGHT COLUMN: ANALYSIS
    with col_data:
        st.markdown("### 🔍 Analysis Results")
        
        # Initializing session state
        if "analysis_result" not in st.session_state:
            st.session_state.analysis_result = ""

        result_container = st.container()

        
        # 1. generating logic (Runs only if data is missing & location is set)
        if st.session_state.analysis_result == "" and location_data['longitude'] is not None:
            try:
                with st.spinner('Analyzing prescription details...'):
                    response_stream = logic.analyze_prescription(uploaded_file, location_data)
                    
                    # Collecting  the kresponse_stream into a single string first
                    full_json_string = ''
                    for chunk in response_stream:
                        full_json_string += chunk.text
                    
                    # Saving raw text to session state immediately
                    st.session_state.analysis_result = full_json_string
                    
            except Exception as e:
                st.error(f"An error occurred during analysis: {e}")


        # 2. Display logic (Runs every time if data exists)
        if st.session_state.analysis_result:
            with result_container:
                st.success("✅ Analysis Complete!")
                
                tab1, tab2 = st.tabs(["📋 Extracted Data", "⚠️ Critical Warnings"])
                
            
                with tab1:
                    try:
                        # Get data from session state
                        json_text = st.session_state.analysis_result
                        
                        # Cleaning json
                        
                        match = re.search(r'(\{.*\})', json_text, re.DOTALL)
                        clean_json = match.group(1) if match else json_text
                        
                        # loading the json
                        data_dict = json.loads(clean_json)
                        
                        # Extracting patient_info and prescription data
                        patient_info = data_dict.get('patient_info', {})
                        prescription_list = data_dict.get('prescription_data', [])
                        
                        # displaying patient_info
                        c1, c2, c3 = st.columns(3)
                        c1.markdown(f"**Patient:** {patient_info.get('Name', 'Not Provided')}")
                        c2.markdown(f"**Age:** {patient_info.get('Age', 'Not Provided')}")
                        c3.markdown(f"**Date:** {patient_info.get('Date', 'Not Provided')}")
                        
                        st.divider()

                        # Display Table
                        if prescription_list:
                            df = pd.DataFrame(prescription_list)
                            st.dataframe(
                                df,
                                column_config={
                                    "Map_link": st.column_config.LinkColumn("Pharmacy Location",display_text="📍 View Map")
                                },
                                use_container_width=True,
                                height=int((len(df)+1)*35+3)
                            )
                        else:
                            st.warning("No prescription data found.")
                            
                        #storing the text tupe data into session again to enable the download action.
                        st.session_state.analysis_result = json.dumps(data_dict, indent=4)

                    except json.JSONDecodeError:
                        st.error("Failed to parse response.")
                        with st.expander("Raw Output"):
                            st.code(st.session_state.analysis_result)

      
                with tab2:
                   
                    if prescription_list:
                        warning_response = logic.analyze_for_warnings(prescription_list)
                        def stream_content(response_warn):
                            for chunk in response_warn:
                                if chunk.text:
                                    yield chunk.text
                        st.write_stream(stream_content(warning_response))
                    else:
                        st.info("Warnings will appear here.")

        
            st.markdown("### Actions")
            b1,b2=st.columns(2)
            with b1:
                st.download_button(
                    label="📥 Download Report",
                    data=st.session_state.analysis_result,
                    file_name="prescription_report.json",
                    mime="application/json",
                    use_container_width=True
                )
            with b2:
                if st.button('Save to Data Base',use_container_width=True):
                    saved_into_db=database.save_to_db(patient_info,prescription_list)
                    st.toast(saved_into_db)



        # 3. PROMPT TO START
        elif location_data['longitude'] is None:
            st.warning('Click **Location Button** to Start Analysis\n')
            

else:
    st.markdown("""
        <div style='text-align: center; margin-top: 50px; color: #aaa;'>
            <h2>👋 Waiting for upload...</h2>
            <p>Please upload a prescription image and **click Location_button**  to view the analysis dashboard.</p>
        </div>
        """, unsafe_allow_html=True)