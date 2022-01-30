Codesigning apps
===================
PyEverywhere automates the codesigning, and now notarization, processes on macOS,
iOS and Android, with Windows support planned.

macOS app code-signing
=======================
On macOS, to support app codesigning, you need an Apple Developer account along
with a Developer ID Application certificate. Once you have that, make sure to set
the following environment variables:

`MAC_CODESIGN_IDENTITY` - the certificate name, typically `Developer ID Application: <your_identity>`.
`MAC_DEV_ID_EMAIL` - the email address associated with your Apple Developer ID.
`MAC_APP_PASSWORD` - App-specific password, see here on how to create https://support.apple.com/en-us/HT204397

Then, the process for creating a codesigned and notarized app is as follows:

```
pew build
pew codesign
pew package
pew notarize [--wait]

Passing --wait to notarize will cause pew to wait until the app has been notarized,
and "staple" the notarization to the package. This ensures that the notarization
is recognized even for offline distribution.

Codesigning with Multi-team Developer Accounts
===============================================
An Apple Developer account may belong to multiple teams. In this case, you need
to let the signing process know which team you're signing on behalf of.

In order to do so, you need to specify what they refer to as a
`notarization provider`. You can get a list of provider names for your account
using the following command:

`xcrun altool --list-providers -u $MAC_DEV_ID_EMAIL -p $MAC_APP_PASSWORD`

Once you've found the correct notarization provider, create a `MAC_NOTARIZATION_PROVIDER` secret with that as the value.

Creating a Github Action for Codesigning (macOS)
=================================================

Step 1: Export your developer ID certificate for upload to Github

Follow the instructions here, up until the step copying the certificate to the clipboard:

https://localazy.com/blog/how-to-automatically-sign-macos-apps-using-github-actions

Step 2: Set up the necessary secrets (i.e. environment variables) for the Github Action

To do this, go to your repo's settings page, then go to the Secrets section. Click the button
to add a new secret, then create the following environment variables:

`MAC_CODESIGN_IDENTITY`, `MAC_DEV_ID_EMAIL`, `MAC_APP_PASSWORD` - see above for details
`KEYCHAIN_PASSWORD` - just a password for the build machine to use, set it to whatever you want.
`MAC_CODESIGN_CERT` - paste the contents of the p12 file into this one.
`P12_PASSWORD` - enter the password you used for the certificate.
