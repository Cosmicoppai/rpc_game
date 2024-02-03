if __name__ == "__main__":

    import tkinter as tk
    from tkinter import messagebox
    from zero import ZeroClient
    from msgspec import Struct

    ZERO_CLIENT = ZeroClient("localhost", 9000)
    _player_token = None
    WINNER_DECLARED = False

    window = tk.Tk()
    window.title("Tic Tac Toe")


    class Move(Struct):
        token: str
        row: int
        col: int


    class MoveStatus(Struct):
        row: int = 0
        col: int = 0
        status: str = "None"
        move_text: str = ""
        reason: str = ""
        game_status: str = ""


    class RegisterPlayers(Struct):
        token: str
        register: bool = False


    def show_error(err: str):
        messagebox.showerror("Error", err)


    def send_move(move: Move):
        return ZERO_CLIENT.call("move", move, return_type=MoveStatus)


    def register_players():
        global _player_token
        resp = ZERO_CLIENT.call("register_players", None, return_type=RegisterPlayers)
        if resp.register:
            _player_token = resp.token
            return True
        else:
            show_error("Lobby is full")
            return False


    def reset():
        ZERO_CLIENT.call('reset', None)
        fetch_data()


    def quit_game():
        ZERO_CLIENT.call('quit_game', _player_token)
        ZERO_CLIENT.close()

    def on_closing():
        quit_game()
        window.quit()


    player_registered = register_players()  # register the player

    try:


        # Create board
        def create_board():
            for i in range(3):
                for j in range(3):
                    button = tk.Button(window, text="", font=("Arial", 50), height=2, width=6, bg="lightblue",
                                       command=lambda row=i, col=j: handle_click(row, col))
                    button.grid(row=i, column=j, sticky="nsew")


        if player_registered:
            create_board()


        # Handle button clicks
        def handle_click(row, col):
            if not window.grid_slaves(row=row, column=col)[0].cget("text"):
                move_resp = send_move(Move(token=_player_token, row=row, col=col))
                update_state(move_resp)
            else:
                show_error("Invalid Move: Cell already occupied")


        def update_state(move_resp):
            if move_resp.status.lower() == "success":
                button = window.grid_slaves(row=move_resp.row, column=move_resp.col)[0]
                button.config(text=move_resp.move_text)
                if move_resp.game_status and not WINNER_DECLARED:
                    declare_winner(move_resp.game_status)
            elif move_resp.status.lower() == "none":
                ...
            else:
                show_error(move_resp.reason)


        def fetch_data():
            move_resp = ZERO_CLIENT.call('fetch_data', None, return_type=MoveStatus)
            update_state(move_resp)
            if not move_resp.game_status:  # stop fetching data if game is over
                window.after(200, fetch_data)


        # Declare the winner and ask to restart the game
        def declare_winner(winner):
            global WINNER_DECLARED
            WINNER_DECLARED = True
            if winner == "tie":
                message = "It's a tie!"
            else:
                message = f"Player {winner} wins!"

            answer = messagebox.askyesno("Game Over", message + " Do you want to restart the game?")

            if answer:
                reset()
                for i in range(3):
                    for j in range(3):
                        button = window.grid_slaves(row=i, column=j)[0]
                        button.config(text="")

                fetch_data()
            else:
                quit_game()
                window.quit()


        if player_registered:
            fetch_data()

        window.protocol("WM_DELETE_WINDOW", on_closing)
        window.mainloop()

    except Exception as e:
        print(e)
        quit_game()
