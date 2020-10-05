from prompt_toolkit.key_binding import KeyBindings

from textomatic import context

kb = KeyBindings()
cmd_kb = KeyBindings()

kb.add("c-c")(lambda e: e.app.exit())
kb.add("tab")(lambda e: e.app.layout.focus_next())
kb.add("s-tab")(lambda e: e.app.layout.focus_previous())


@kb.add("c-t")
def change_boxes_orientation(_):
    ctx = context.get()
    ctx.box_veritcal_orientation = not ctx.box_veritcal_orientation


@kb.add("c-o")
def exit_and_print_output(_):
    ctx = context.get()
    ctx.print_output_on_exit = True
    ctx.app.exit()


@kb.add("c-p")
def copy_output_to_clipboard(_):
    ctx = context.get()
    ctx.app.clipboard.set_text(ctx.output_buffer.text)
    ctx.copied_to_clipboard = True

    def off():
        ctx.copied_to_clipboard = False

    ctx.app.loop.call_later(0.1, off)


@kb.add("f1")
def toggle_help(_):
    ctx = context.get()
    ctx.display_help = not ctx.display_help


@kb.add("c-l")
def toggle_live(_):
    ctx = context.get()
    ctx.live = not ctx.live


@kb.add("c-r")
def run1(_):
    ctx = context.get()
    ctx.process_fn("run")


cmd_kb.add("c-m")(lambda _: run1(_))
