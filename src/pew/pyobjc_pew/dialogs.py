import AppKit


def open_file_dialog(callback):
    openPanel = AppKit.NSOpenPanel.openPanel()

    openPanel.setCanChooseFiles_(True)
    openPanel.setCanChooseDirectories_(False)

    if openPanel.runModal() == AppKit.NSOKButton:
        fileString = openPanel.URL().relativePath()
        callback(fileString)
