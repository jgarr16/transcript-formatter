#!/usr/bin/env bash
# Transcript Formatter — macOS installer
# Creates the Automator Quick Action (Service) and verifies Python deps.

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MAIN_PY="$SCRIPT_DIR/main.py"
SERVICE_NAME="Format Transcript"
SERVICE_DIR="$HOME/Library/Services"
WORKFLOW_PATH="$SERVICE_DIR/${SERVICE_NAME}.workflow"
CONTENTS_DIR="$WORKFLOW_PATH/Contents"

# ── Python check ──────────────────────────────────────────────────────────────
PYTHON=$(command -v python3 || true)
if [ -z "$PYTHON" ]; then
    echo "Error: python3 not found. Install it from https://python.org or via Homebrew."
    exit 1
fi
echo "Using Python: $PYTHON ($($PYTHON --version))"

# ── Optional dependencies ─────────────────────────────────────────────────────
echo ""
echo "Installing optional AI dependencies (you can skip any you don't need)..."
read -r -p "Install anthropic SDK? [y/N] " ans
[[ "$ans" =~ ^[Yy]$ ]] && $PYTHON -m pip install --quiet anthropic

read -r -p "Install openai SDK? [y/N] " ans
[[ "$ans" =~ ^[Yy]$ ]] && $PYTHON -m pip install --quiet openai

read -r -p "Install requests (needed for Ollama)? [y/N] " ans
[[ "$ans" =~ ^[Yy]$ ]] && $PYTHON -m pip install --quiet requests

# ── Build Automator workflow ──────────────────────────────────────────────────
echo ""
echo "Installing macOS Service: '${SERVICE_NAME}'"

mkdir -p "$CONTENTS_DIR"

# The shell command that runs inside the Automator action.
# stdin = selected text passed by macOS Services architecture.
SHELL_CMD="$PYTHON \"$MAIN_PY\" --notify 2>>/tmp/transcript_formatter.log"

cat > "$CONTENTS_DIR/document.wflow" << PLIST_EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
	<key>AMApplicationBuild</key>
	<string>521.1</string>
	<key>AMApplicationVersion</key>
	<string>2.10</string>
	<key>AMDocumentVersion</key>
	<string>2</string>
	<key>actions</key>
	<array>
		<dict>
			<key>action</key>
			<dict>
				<key>AMAccepts</key>
				<dict>
					<key>Container</key>
					<string>List</string>
					<key>Optional</key>
					<true/>
					<key>Types</key>
					<array>
						<string>com.apple.cocoa.string</string>
					</array>
				</dict>
				<key>AMActionVersion</key>
				<string>2.0.3</string>
				<key>AMApplication</key>
				<array>
					<string>Automator</string>
				</array>
				<key>AMParameterProperties</key>
				<dict>
					<key>COMMAND_STRING</key>
					<dict/>
					<key>CheckedForUserDefaultShell</key>
					<dict/>
					<key>inputMethod</key>
					<dict/>
					<key>shell</key>
					<dict/>
					<key>source</key>
					<dict/>
				</dict>
				<key>AMProvides</key>
				<dict>
					<key>Container</key>
					<string>List</string>
					<key>Types</key>
					<array>
						<string>com.apple.cocoa.string</string>
					</array>
				</dict>
				<key>ActionBundlePath</key>
				<string>/System/Library/Automator/Run Shell Script.action</string>
				<key>ActionName</key>
				<string>Run Shell Script</string>
				<key>ActionParameters</key>
				<dict>
					<key>COMMAND_STRING</key>
					<string>$SHELL_CMD</string>
					<key>CheckedForUserDefaultShell</key>
					<true/>
					<key>inputMethod</key>
					<integer>1</integer>
					<key>shell</key>
					<string>/bin/bash</string>
					<key>source</key>
					<string></string>
				</dict>
				<key>BundleIdentifier</key>
				<string>com.apple.RunShellScript</string>
				<key>CFBundleVersion</key>
				<string>2.0.3</string>
				<key>CanShowSelectedItemsWhenRun</key>
				<false/>
				<key>CanShowWhenRun</key>
				<true/>
				<key>Category</key>
				<array>
					<string>AMCategoryUtilities</string>
				</array>
				<key>Class Name</key>
				<string>RunShellScriptAction</string>
				<key>InputUUID</key>
				<string>F0E6B5D4-C3B2-4A1F-9E8D-7C6B5A4F3E2D</string>
				<key>Keywords</key>
				<array>
					<string>Shell</string>
					<string>Script</string>
					<string>Command</string>
					<string>Run</string>
					<string>Unix</string>
				</array>
				<key>OutputUUID</key>
				<string>A1B2C3D4-E5F6-7890-ABCD-EF1234567890</string>
				<key>UUID</key>
				<string>12345678-1234-1234-1234-123456789012</string>
				<key>UnlockEtcHosts</key>
				<false/>
				<key>arguments</key>
				<dict/>
				<key>isViewVisible</key>
				<integer>1</integer>
				<key>location</key>
				<string>309.5:253.0</string>
				<key>nickname</key>
				<string>Run Shell Script</string>
				<key>selectedHandlerInputParameter</key>
				<string>input</string>
			</dict>
		</dict>
	</array>
	<key>connectors</key>
	<dict/>
	<key>workflowMetaData</key>
	<dict>
		<key>serviceInputTypeIdentifier</key>
		<string>com.apple.Automator.text</string>
		<key>serviceOutputTypeIdentifier</key>
		<string>com.apple.Automator.nothing</string>
		<key>serviceProcessesInput</key>
		<false/>
		<key>workflowTypeIdentifier</key>
		<string>com.apple.Automator.servicesMenu</string>
	</dict>
</dict>
</plist>
PLIST_EOF

echo "Workflow written to: $WORKFLOW_PATH"

# ── Reload Services ───────────────────────────────────────────────────────────
# Tell macOS to refresh the Services menu
/System/Library/CoreServices/pbs -update 2>/dev/null || true

echo ""
echo "Done! The '${SERVICE_NAME}' service is now available."
echo ""
echo "Next steps:"
echo "  1. Run config setup:   python3 \"$MAIN_PY\" --config"
echo "  2. Select text in any app, right-click → Services → '${SERVICE_NAME}'"
echo "  3. Check output in:    ~/Documents/Transcripts  (or your configured folder)"
echo ""
echo "Tip: If the service doesn't appear immediately, log out and back in,"
echo "     or go to System Settings → Keyboard → Keyboard Shortcuts → Services"
echo "     and make sure '${SERVICE_NAME}' is checked."
