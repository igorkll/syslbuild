from __main__ import *
import __main__

def bootlogo_add_message_handlers(bootlogo_script):
    bootlogo_script += """message_sprite = Sprite();
message_sprite.SetOpacity(0);
message_sprite.SetZ(10000);

status_sprite = Sprite();
status_sprite.SetOpacity(0);
status_sprite.SetZ(10000);

MESSAGE_FONT  = "Plymouth 24";
MESSAGE_COLOR = [1, 1, 1, 1];

STATUS_FONT   = "Plymouth 12";
STATUS_COLOR  = [0.8, 0.8, 0.8, 1];

MESSAGE_Y     = 0.72;
STATUS_Y      = 0.80;

fun show_message(text)
{
    if (text == "")
    {
        message_sprite.SetOpacity(0);
        return;
    }

    img = Image.Text(text,
                     MESSAGE_COLOR[0], MESSAGE_COLOR[1],
                     MESSAGE_COLOR[2], MESSAGE_COLOR[3],
                     MESSAGE_FONT);

    x = Window.GetWidth() / 2 - img.GetWidth() / 2;
    y = Window.GetHeight() * MESSAGE_Y;

    message_sprite.SetImage(img);
    message_sprite.SetPosition(x, y, 10000);
    message_sprite.SetOpacity(1);
}

fun show_status(text)
{
    if (text == "")
    {
        status_sprite.SetOpacity(0);
        return;
    }

    img = Image.Text(text,
                     STATUS_COLOR[0], STATUS_COLOR[1],
                     STATUS_COLOR[2], STATUS_COLOR[3],
                     STATUS_FONT);

    x = Window.GetWidth() / 2 - img.GetWidth() / 2;
    y = Window.GetHeight() * STATUS_Y;

    status_sprite.SetImage(img);
    status_sprite.SetPosition(x, y, 10000);
    status_sprite.SetOpacity(1);
}


fun hide_message()
{
    message_sprite.SetOpacity(0);
}

Plymouth.SetMessageFunction(show_message);
Plymouth.SetUpdateStatusFunction(show_status);
Plymouth.SetHideMessageFunction(hide_message);"""
    
    return bootlogo_script

def setup_bootlogo():
    bootlogo_files = os.path.join(__main__.path_temp_syslbuild, "files", "bootlogo")
    project_logo_path = os.path.join(__main__.path_resources, "logo.png")
    project_logo_updating_path = os.path.join(__main__.path_resources, "logo_updating.png")

    if __main__.current_project.boot_splash:
        copyFile(os.path.join(bootlogo_files, "bootlogo.plymouth"), "gnuboxmaker/bootlogo.plymouth")
        copyFile(os.path.join(bootlogo_files, "logo.png"), project_logo_path)
        copyFile(os.path.join(bootlogo_files, "logo_updating.png"), project_logo_updating_path)

    if __main__.current_project.splash_mode == "fill":
        scale_code = f"""scaled_width = window_width;
scaled_height = window_height;"""
    elif __main__.current_project.splash_mode == "center":
        scale_code = f"""scaled_width = img_width;
scaled_height = img_height;"""
    elif __main__.current_project.splash_mode == "cover":
        scale_code = f"""img_scale = Math.Max(window_width / img_width, window_height / img_height);
scaled_width = Math.Int(img_width * img_scale);
scaled_height = Math.Int(img_height * img_scale);"""
    else:
        scale_code = f"""img_scale = Math.Min(window_width / img_width, window_height / img_height);
scaled_width = Math.Int(img_width * img_scale);
scaled_height = Math.Int(img_height * img_scale);"""

    bootlogo_script = f"""
mode = Plymouth.GetMode();
if (mode == "system-upgrade") {{
    Window.SetBackgroundTopColor({__main__.current_project.splash_updating_bg});
    Window.SetBackgroundBottomColor({__main__.current_project.splash_updating_bg});

    image = Image("logo_updating.png");
}} else {{
    Window.SetBackgroundTopColor({__main__.current_project.splash_bg});
    Window.SetBackgroundBottomColor({__main__.current_project.splash_bg});

    image = Image("logo.png");
}}

window_width = Window.GetWidth();
window_height = Window.GetHeight();
img_width = image.GetWidth();
img_height = image.GetHeight();

{scale_code}

scaled_width = scaled_width * {__main__.current_project.splash_scale};
scaled_height = scaled_height * {__main__.current_project.splash_scale};

scaled_image = image.Scale(scaled_width, scaled_height);
x = (window_width - scaled_width) / 2;
y = (window_height - scaled_height) / 2;

image_sprite = Sprite(scaled_image);
image_sprite.SetX(x);
image_sprite.SetY(y);
image_sprite.SetZ(-1);"""

    if __main__.current_project.plymouth_allow_render_text:
        bootlogo_script = bootlogo_add_message_handlers(bootlogo_script + "\n")

    writeText(os.path.join(bootlogo_files, "bootlogo.script"), bootlogo_script)
