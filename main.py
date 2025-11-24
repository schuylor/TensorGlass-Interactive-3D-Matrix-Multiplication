import matplotlib
matplotlib.use("TkAgg")   # Prevent PyCharm backend bugs
import matplotlib.pyplot as plt
import numpy as np
from mpl_toolkits.mplot3d import Axes3D

# --- Color Definitions (RGBA) ---
# Glass effect (inactive)
COL_GLASS = (0.85, 0.85, 0.85, 0.08)  # Very transparent gray
COL_MAT_OFF = (0.7, 0.7, 0.7, 0.15)  # Semi-transparent gray (inactive matrix cells)

# Solid highlights (active)
COL_TENSOR_ACT = (1.0, 0.2, 0.2, 1.0)  # Active computation fiber (red)
COL_INPUT_ACT = (0.0, 0.8, 0.2, 1.0)  # Highlighted A row / B column (green)
COL_RES_ACT = (0.0, 0.4, 1.0, 1.0)  # Highlighted C cell (blue)


class TensorCalculator:
    def __init__(self, I, J, K):
        self.I = I  # Number of rows in A / rows in C
        self.J = J  # Number of columns in A / rows in B (summation dimension)
        self.K = K  # Number of columns in B / columns in C

        self.selected_idx = None  # Currently selected result index (i, k)

        # Create drawing canvas
        self.fig = plt.figure(figsize=(12, 9))
        self.ax = self.fig.add_subplot(111, projection='3d')
        self.ax.set_proj_type('ortho')  # Orthographic projection (remove perspective distortion)

        # Bind mouse pick event
        self.fig.canvas.mpl_connect('pick_event', self.on_pick)

        self.draw()

    def draw(self):
        self.ax.clear()
        self.ax.set_axis_off()

        title = f"Tensor Calculator: A({self.I}x{self.J}) • B({self.J}x{self.K}) = C({self.I}x{self.K})\n"
        sub = "Click on any BLUE/GRAY block on the TOP layer"
        self.ax.set_title(title + sub, fontsize=14)

        # ---------------------------------------------------------
        # 1. Draw the tensor core (middle computation blocks)
        # Coordinate mapping: i->x, k->y, j->z (vertical axis = summation)
        # ---------------------------------------------------------
        for i in range(self.I):
            for k in range(self.K):
                # Determine whether this fiber is activated
                is_fiber_active = False
                if self.selected_idx and self.selected_idx == (i, k):
                    is_fiber_active = True

                for j in range(self.J):
                    # Choose color
                    if is_fiber_active:
                        color = COL_TENSOR_ACT
                        edge = 'k'
                        lw = 0.5
                    else:
                        color = COL_GLASS
                        edge = (0.6, 0.6, 0.6, 0.1)
                        lw = 0.1

                    # Draw cube
                    self.ax.bar3d(i, k, j, 0.8, 0.8, 0.8,
                                  color=color, edgecolor=edge, linewidth=lw, shade=True)

        # ---------------------------------------------------------
        # 2. Draw matrix A (input) on the left side
        # Logical position: (i, j). Visual: x=i, y=offset, z=j
        # ---------------------------------------------------------
        offset_A_y = -1.5
        for i in range(self.I):
            # Check whether this row is selected
            is_row_active = (self.selected_idx is not None and self.selected_idx[0] == i)

            for j in range(self.J):
                color = COL_INPUT_ACT if is_row_active else COL_MAT_OFF
                alpha_txt = 1.0 if is_row_active else 0.3

                # Draw flat block
                self.ax.bar3d(i, offset_A_y, j, 0.8, 0.2, 0.8,
                              color=color, edgecolor='k', linewidth=0.5, shade=True)

                # Label A_i,j
                self.ax.text(i + 0.4, offset_A_y - 0.2, j + 0.4, f"A{i + 1},{j + 1}",
                             ha='center', va='center', fontsize=8, color='black', alpha=alpha_txt)

        # ---------------------------------------------------------
        # 3. Draw matrix B (input) on the back/right side
        # Logical position: (j, k). Visual: x=offset, y=k, z=j
        # ---------------------------------------------------------
        offset_B_x = self.I + 0.5
        for k in range(self.K):
            # Check whether this column is selected
            is_col_active = (self.selected_idx is not None and self.selected_idx[1] == k)

            for j in range(self.J):
                color = COL_INPUT_ACT if is_col_active else COL_MAT_OFF
                alpha_txt = 1.0 if is_col_active else 0.3

                self.ax.bar3d(offset_B_x, k, j, 0.2, 0.8, 0.8,
                              color=color, edgecolor='k', linewidth=0.5, shade=True)

                self.ax.text(offset_B_x + 0.4, k + 0.4, j + 0.4, f"B{j + 1},{k + 1}",
                             ha='center', va='center', fontsize=8, color='black', alpha=alpha_txt)

        # ---------------------------------------------------------
        # 4. Draw matrix C (result) on the top layer (interactive layer)
        # Logical: (i, k). Visual: x=i, y=k, z=offset
        # ---------------------------------------------------------
        offset_C_z = self.J + 0.5

        # Store coordinates for invisible picking layer
        picker_x = []
        picker_y = []
        picker_data = []

        for i in range(self.I):
            for k in range(self.K):
                # Check if selected
                is_cell_active = (self.selected_idx == (i, k))

                color = COL_RES_ACT if is_cell_active else COL_MAT_OFF

                # Draw top block
                self.ax.bar3d(i, k, offset_C_z, 0.8, 0.8, 0.2,
                              color=color, edgecolor='k', linewidth=0.5, shade=True)

                # Label C_i,k
                txt_weight = 'bold' if is_cell_active else 'normal'
                txt_col = 'white' if is_cell_active else 'black'
                self.ax.text(i + 0.4, k + 0.4, offset_C_z + 0.3, f"C{i + 1},{k + 1}",
                             ha='center', va='center', fontsize=9, color=txt_col, fontweight=txt_weight)

                # Data for invisible picker
                picker_x.append(i + 0.4)
                picker_y.append(k + 0.4)
                picker_data.append((i, k))

        # Invisible picking scatter plot
        # bar3d picker is unreliable; scatter is stable
        scat = self.ax.scatter(picker_x, picker_y, [offset_C_z + 0.5] * len(picker_x),
                               s=1000, alpha=0.0, picker=True)
        scat.custom_data = picker_data

        # Auxiliary text + view settings
        self.ax.text(-1, -2, 0, "Dimension i (Rows)", color='green')
        self.ax.text(self.I + 1, self.K + 1, 0, "Dimension k (Cols)", color='purple')
        self.ax.text(-1, -1, self.J / 2, "Dimension j (Sum)", color='red', rotation=90)

        # Axis limits
        limit = max(self.I, self.J, self.K)
        self.ax.set_xlim(-1, limit + 1)
        self.ax.set_ylim(-2, limit + 1)
        self.ax.set_zlim(0, limit + 2)

        # Initial camera angle
        self.ax.view_init(elev=25, azim=-60)
        self.fig.canvas.draw_idle()

    def on_pick(self, event):
        # Handle mouse click event
        if event.artist.get_alpha() == 0.0:  # Ensure clicking only invisible picker layer
            ind = event.ind[0]
            data = event.artist.custom_data

            new_selection = data[ind]
            print(f"User clicked: C{new_selection[0] + 1},{new_selection[1] + 1}")

            self.selected_idx = new_selection
            self.draw()


def get_user_input():
    print("--- Matrix Tensor Calculator ---")
    try:
        print("Define Matrix Sizes:")
        i_in = int(input("Enter size I (Rows of A) [default 2]: ") or 2)
        j_in = int(input("Enter size J (Common Dim) [default 2]: ") or 2)
        k_in = int(input("Enter size K (Cols of B) [default 2]: ") or 2)

        # Limit sizes to avoid extreme lag
        if i_in > 6 or j_in > 6 or k_in > 6:
            print("Warning: Large dimensions might be slow.")

        return i_in, j_in, k_in
    except ValueError:
        print("Invalid input, using defaults 2x2x2.")
        return 2, 2, 2


if __name__ == "__main__":
    # 1. Get user input
    I, J, K = get_user_input()

    # 2. Start visualization
    app = TensorCalculator(I, J, K)
    plt.show()
