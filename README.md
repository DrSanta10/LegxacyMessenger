# LegxacyMessenger

Welcome to LegxacyMessenger - a python-based client-server application using socket programming.

The application can be used both in the terminal and in the dedicated GUI.

Terminal procedure:
1. Run the server.py file in a dedicated terminal window.
2. Run the client.py file in a separate terminal window (up to 5 terminals)

General message structure:
/(command) (client_name) (body)
/(command) (group_name) (body)

Terminal navigation:
'/msg' to send a message
'/group' to send a message to a group
'/create' to create a group
'/join' to join a group
'/leave' to leave a group
'/quit' to quit the chat system