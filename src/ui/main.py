import flet as ft
import json
import time

# Hardcoded JSON object
DUMMY_DATA = {
    "file_path": "C:/Users/aryah/Documents/sample_document.pdf",
    "extension": ".pdf",
    "summaries": {
        "tldr": "Quickly explains the core ideas behind attention strategies.",
        "bullets": [
            "Defines ADHD in simple terms",
            "Lists common behavioral patterns",
            "Shares techniques for improved focus"
        ],
        "paragraph": [
            "The document gives a concise yet informative overview of Attention Deficit Hyperactivity Disorder (ADHD). "
            "It highlights symptoms, diagnosis methods, and behavioral therapy options for individuals, especially children. "
            "The emphasis is on early detection and practical coping mechanisms to manage attention-related challenges effectively."
        ]
    },
    "file_content": (
        "ADHD stands for Attention Deficit Hyperactivity Disorder. It is a neurological disorder that affects a person’s "
        "ability to focus, control impulses, and maintain attention. Children and adults with ADHD often struggle with "
        "organization and time management. This guide walks through essential ADHD symptoms, diagnosis procedures, and coping "
        "strategies such as creating structured environments, using reminders, and building positive routines."
    )
}

def main(page: ft.Page):
    page.title = "ADHD Reader"
    page.scroll = "auto"
    page.window_width = 900
    page.window_height = 800
    page.fonts = {"lexend": "https://fonts.googleapis.com/css2?family=Lexend&display=swap"}
    page.theme_mode = ft.ThemeMode.LIGHT

    # Font size and theme settings
    font_size_slider = ft.Slider(min=12, max=24, divisions=6, label="{value}px", value=16)
    theme_switch = ft.Switch(label="Dark Mode")

    paragraph_visible = ft.Ref[ft.Text]()
    toggle_btn = ft.Ref[ft.ElevatedButton]()

    def toggle_paragraph(e):
        paragraph_visible.current.visible = not paragraph_visible.current.visible
        toggle_btn.current.text = "Hide Full Summary" if paragraph_visible.current.visible else "Show Full Summary"
        page.update()

    def change_theme(e):
        page.theme_mode = ft.ThemeMode.DARK if theme_switch.value else ft.ThemeMode.LIGHT
        page.update()

    def update_font_size(e):
        for ctrl in summaries:
            ctrl.size = font_size_slider.value
        page.update()

    # Welcome header
    page.add(
        ft.Text("✨ Welcome to ADHD Reader ✨", size=32, weight="bold", font_family="lexend", color=ft.colors.BLUE_900)
    )

    # Loading animation
    loading = ft.Text("Loading your file...", size=20, italic=True)
    page.add(loading)
    page.update()
    time.sleep(2)
    page.controls.remove(loading)

    # File Info Display
    page.add(ft.Text("📄 File Info", size=20, weight="bold", font_family="lexend"))
    page.add(ft.Text(json.dumps({
        "file_path": DUMMY_DATA["file_path"],
        "extension": DUMMY_DATA["extension"]
    }, indent=4), font_family="Courier New", selectable=True))

    # Font size + theme toggle row
    page.add(
        ft.Row([
            ft.Text("Font size", font_family="lexend"),
            font_size_slider,
            ft.VerticalDivider(),
            theme_switch
        ])
    )
    theme_switch.on_change = change_theme
    font_size_slider.on_change = update_font_size

    # Summaries
    summaries = []

    # TL;DR
    page.add(ft.Text("📌 TL;DR", size=20, weight="bold", font_family="lexend"))
    tldr = ft.Text(DUMMY_DATA["summaries"]["tldr"], font_family="lexend", size=font_size_slider.value)
    page.add(tldr)
    summaries.append(tldr)

    # Bullet points
    page.add(ft.Text("🔹 3-Point Summary", size=20, weight="bold", font_family="lexend"))
    for point in DUMMY_DATA["summaries"]["bullets"]:
        bullet = ft.Text(f"• {point}", font_family="lexend", size=font_size_slider.value)
        page.add(bullet)
        summaries.append(bullet)

    # Full paragraph summary
    page.add(ft.Text("🧾 Full Summary", size=20, weight="bold", font_family="lexend"))
    paragraph = ft.Text(
        DUMMY_DATA["summaries"]["paragraph"],
        font_family="lexend",
        size=font_size_slider.value,
        visible=False,
        ref=paragraph_visible
    )
    page.add(paragraph)
    page.add(ft.ElevatedButton("Show Full Summary", ref=toggle_btn, on_click=toggle_paragraph))
    summaries.append(paragraph_visible.current)

    # File content display
    page.add(ft.Text("📘 File Content", size=20, weight="bold", font_family="lexend"))
    page.add(
        ft.Container(
            ft.Text(DUMMY_DATA["file_content"], font_family="Consolas", size=14, selectable=True),
            bgcolor=ft.colors.GREY_100,
            padding=15,
            border_radius=10,
            expand=True
        )
    )

ft.app(target=main)
