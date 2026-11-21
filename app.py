import streamlit as st
import cv2
import numpy as np
from streamlit_drawable_canvas import st_canvas
from PIL import Image
import json
from pathlib import Path

# Location of our saved reference colors
reference_file = Path(
Path(__file__).parent / "reference_colors.json"
)

# Load the reference colors
with open(reference_file, "r") as file:
    saved_colors = json.load(file)

# Convert the colors into NumPy arrays
reference_colors = {
    label: np.array(color)
    for label, color in saved_colors.items()
}

st.title("Bandage Color Scanner")

st.write(
    "Upload a photo of your bandage to begin "
    "analyzing its color."
)

uploaded_file = st.file_uploader(
    "Choose a bandage photo",
    type=["jpg", "jpeg", "png"]
)

if uploaded_file is not None:

    # Display the uploaded photo
    st.image(
        uploaded_file,
        caption="Your uploaded photo",
        use_container_width=True
    )

    # Read the uploaded image
    file_bytes = np.asarray(
        bytearray(uploaded_file.getvalue()),
        dtype=np.uint8
    )

    image = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)

    # Convert the image from OpenCV format to a format for display
    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    pil_image = Image.fromarray(image_rgb)

    # Show a rectangle drawing tool
    canvas_result = st_canvas(
        background_image=pil_image,
        drawing_mode="rect",
        stroke_width=3,
        stroke_color="#00FF00",
        fill_color="rgba(0, 255, 0, 0.1)",
        height=400,
        width=600,
        key="bandage_selector",
    )

    # Calculate the average color inside the rectangle
    if canvas_result.json_data is not None:
        objects = canvas_result.json_data["objects"]

        if len(objects) > 0:
            # Get the most recently drawn rectangle
            rectangle = objects[-1]

            # Get the rectangle's position and size
            left = int(rectangle["left"])
            top = int(rectangle["top"])
            width = int(rectangle["width"] * rectangle.get("scaleX", 1))
            height = int(rectangle["height"] * rectangle.get("scaleY", 1))

            # Convert rectangle coordinates to image coordinates
            scale_x = image.shape[1] / 600
            scale_y = image.shape[0] / 400

            x1 = max(0, int(left * scale_x))
            y1 = max(0, int(top * scale_y))
            x2 = min(image.shape[1], int((left + width) * scale_x))
            y2 = min(image.shape[0], int((top + height) * scale_y))

            # Measure only the selected part of the original image
            selected_area = image[y1:y2, x1:x2]

            if selected_area.size > 0:
                average_color = np.mean(selected_area, axis=(0, 1))
                st.subheader("Selected Area Color")
                st.write("Average color (BGR):", average_color)
            else:
                st.warning("Please draw a larger rectangle.")
        else:
            st.info("Draw a rectangle around the colored gauze to measure it.")
    else:
        st.info("Draw a rectangle around the colored gauze to measure it.")


    # Show the result
    st.subheader("Color Measurement")
    st.write("Average color (BGR):", average_color)
    
    
    # Compare the measured color with reference colors
    st.subheader("Closest Reference Color")

    smallest_difference = float("inf")
    closest_reference = None

    for label, reference_color in reference_colors.items():
        difference = np.linalg.norm(
            average_color - reference_color
        )
        
        if difference < smallest_difference:
            smallest_difference = difference
            closest_reference = label

        st.write(f"{label}: difference = {difference:.2f}")

    st.success(f"Closest match: {closest_reference}")
    st.write(f"Color difference: {smallest_difference:.2f}")
    
    # Show the color in RGB order too
    blue, green, red = average_color
    st.write(
        f"Red: {red:.1f}, "
        f"Green: {green:.1f}, "
        f"Blue: {blue:.1f}"
    )
