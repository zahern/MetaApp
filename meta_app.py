import pandas as pd
import PySimpleGUI as sg

class DecisionApp:
    def __init__(self):
        self.data = None
        self.current_index = 0
        self.decisions = []
        self.grouped_column = None
        self.panel_column = None
        self.y_column = None
        self.column_names = []
        self.column_info = {}
        self.column_distributions = {}
        self.column_transformations = {}

        # Define the layout with initial empty and disabled states
        layout = [
            [sg.Text("Load a CSV file to continue.")],
            [sg.Button("Load CSV")],
            [sg.Text("", size=(40, 1), key="-MESSAGE-")],
            [sg.Text("Grouped Column: "), sg.Combo(["None"], key="-GROUPED-")],
            [sg.Text("Panel Column: "), sg.Combo(["None"], key="-PANEL-")],
            [sg.Text("Y Column: "), sg.Combo([], key="-Y-")],
            [sg.Button("Set Columns"), sg.Button("Next"), sg.Button("Save Decisions")],
            [sg.Text("Current Column: ", size=(20, 1)), sg.Text("", key="-CURRENT-COLUMN-")],
            [sg.Text("", size=(20, 1), key="-DISPLAY-COLUMN-")],
            [sg.Text("", size=(40, 1), key="-COLUMN-INFO-")],
            [
                sg.Listbox(values=[], select_mode=sg.LISTBOX_SELECT_MODE_MULTIPLE, key="-DISTRIBUTIONS-", size=(30, 6)),
                sg.Button("Remove Selected Distribution", disabled=True),
                sg.Button("Add Distribution", disabled=True)
            ],
            [
                sg.Listbox(values=[], select_mode=sg.LISTBOX_SELECT_MODE_MULTIPLE, key="-TRANSFORMATIONS-", size=(30, 6)),
                sg.Button("Remove Selected Transformation", disabled=True),
                sg.Button("Add Transformation", disabled=True)
            ],
            [sg.Checkbox("Level 1", key="-LEVEL1-", default=True), sg.Text("Off")],
            [sg.Checkbox("Level 2", key="-LEVEL2-", default=True), sg.Text("Fixed Effects")],
            [sg.Checkbox("Level 3", key="-LEVEL3-", default=True), sg.Text("Random Parameters")],
            [sg.Checkbox("Level 4", key="-LEVEL4-", default=True), sg.Text("Correlated Random Parameters in Means")],
            [sg.Checkbox("Level 5", key="-LEVEL5-", disabled=True), sg.Text("Grouped Random Parameters")],
            [sg.Checkbox("Level 6", key="-LEVEL6-", default=True), sg.Text("Heterogeneity in Means")]
        ]

        self.window = sg.Window("METACOUNTREGRESSOR: PREPROCESS DECISIONS", layout)

    def load_csv(self):
        file_path = sg.popup_get_file("Select a CSV file", file_types=(("CSV Files", "*.csv"),))
        if file_path:
            try:
                self.data = pd.read_csv(file_path, encoding='utf-8', on_bad_lines='warn')
                self.current_index = 0
                self.decisions = []

                # Store all column names
                self.column_names = self.data.columns.tolist()

                # Update the combo boxes with column names
                self.window["-Y-"].update(values=self.column_names)

                # Update grouped and panel columns with "None" option
                self.window["-GROUPED-"].update(values=["None"] + self.column_names)
                self.window["-PANEL-"].update(values=["None"] + self.column_names)

                # Calculate column characteristics: type, min, max
                self.column_info = {}
                for col in self.column_names:
                    self.column_info[col] = {
                        "type": str(self.data[col].dtype),
                        "min": self.data[col].min(),
                        "max": self.data[col].max()
                    }

                sg.popup("CSV loaded successfully.")
            except Exception as e:
                sg.popup_error(f"Failed to load CSV: {e}")

    def set_columns(self):
        self.grouped_column = self.window["-GROUPED-"].get()
        self.panel_column = self.window["-PANEL-"].get()
        self.y_column = self.window["-Y-"].get()

        if not self.y_column:
            sg.popup_warning("Y Column must be selected.")
            return

        self.columns_to_process = [
            col for col in self.column_names
            if col not in [self.y_column, self.grouped_column, self.panel_column]
        ]

        if not self.columns_to_process:
            sg.popup_warning("No columns to process. Please select valid columns.")
            return

        self.current_index = 0
        self.show_column()

    def show_column(self):
        if self.current_index < len(self.columns_to_process):
            current_column = self.columns_to_process[self.current_index]
            self.window["-CURRENT-COLUMN-"].update(current_column)
            self.window["-DISPLAY-COLUMN-"].update(current_column)

            info = self.column_info[current_column]
            self.window["-COLUMN-INFO-"].update(f"Type: {info['type']}, Min: {info['min']}, Max: {info['max']}")

            # Initialize distributions for the current column if not set
            if current_column not in self.column_distributions:
                self.column_distributions[current_column] = ["Normal", "Triangular", "Uniform"]

            self.window["-DISTRIBUTIONS-"].update(values=self.column_distributions[current_column])

            # Initialize transformations for the current column if not set
            if current_column not in self.column_transformations:
                self.column_transformations[current_column] = ['no', 'normalise', 'log', 'sqrt', 'arcsinh']  # Start with no transformations

            self.window["-TRANSFORMATIONS-"].update(values=self.column_transformations[current_column])

            # Enable buttons for distributions and transformations
            self.window["Remove Selected Distribution"].update(disabled=False)
            self.window["Add Distribution"].update(disabled=False)
            self.window["Remove Selected Transformation"].update(disabled=False)
            self.window["Add Transformation"].update(disabled=False)

            for i in range(1, 7):
                self.window[f"-LEVEL{i}-"].update(True)  # Set all to True

            # Disable Level 5 if no grouped term is selected
            if self.grouped_column == "None":
                self.window["-LEVEL5-"].update(disabled=True)
            else:
                self.window["-LEVEL5-"].update(disabled=False)

            self.window["-MESSAGE-"].update(f"Processing column: {current_column}...")
        else:
            sg.popup("End", "No more columns to process!")

    def next_column(self):
        if self.current_index < len(self.columns_to_process):
            decisions = [self.window[f"-LEVEL{i}-"].get() for i in range(1, 7)]
            current_column = self.columns_to_process[self.current_index]
            distributions = self.column_distributions[current_column]
            transformations = self.column_transformations[current_column]  # Get transformations
            self.decisions.append((current_column, *decisions, distributions, transformations))
            self.current_index += 1
            self.show_column()
        else:
            sg.popup("End", "No more columns to process!")

    def save_decisions(self):
        if self.decisions:
            output_df = pd.DataFrame(self.decisions, columns=["Column"] + [f"Level {i}" for i in range(1, 7)] + ["Distributions", "Transformations"])
            output_file_path = sg.popup_get_file("Save decisions as", save_as=True, file_types=(("CSV Files", "*.csv"),))
            if output_file_path:
                output_df.to_csv(output_file_path, index=False)
                sg.popup("Success", "Decisions saved successfully!")
                self.select_algorithm()
        else:
            sg.popup_warning("Warning", "No decisions to save!")

    def remove_distribution(self):
        selected = self.window["-DISTRIBUTIONS-"].get_indexes()
        current_column = self.columns_to_process[self.current_index]
        if selected:
            for index in sorted(selected, reverse=True):
                del self.column_distributions[current_column][index]
            self.window["-DISTRIBUTIONS-"].update(values=self.column_distributions[current_column])

    def add_distribution(self):
        current_column = self.columns_to_process[self.current_index]
        new_distribution = sg.popup_get_text("Enter distribution name (Normal, Triangular, Uniform):")
        if new_distribution in ["Normal", "Triangular", "Uniform"]:
            if new_distribution not in self.column_distributions[current_column]:
                self.column_distributions[current_column].append(new_distribution)
                self.window["-DISTRIBUTIONS-"].update(values=self.column_distributions[current_column])
            else:
                sg.popup_warning("Distribution already exists.")

    def remove_transformation(self):
        selected = self.window["-TRANSFORMATIONS-"].get_indexes()
        current_column = self.columns_to_process[self.current_index]
        if selected:
            for index in sorted(selected, reverse=True):
                del self.column_transformations[current_column][index]
            self.window["-TRANSFORMATIONS-"].update(values=self.column_transformations[current_column])

    def add_transformation(self):
        current_column = self.columns_to_process[self.current_index]
        new_transformation = sg.popup_get_text("Enter transformation name (No, Sqrt, Normalize, Log, Arcsinh):")
        if new_transformation in ["No", "Sqrt", "Normalize", "Log", "Arcsinh"]:
            if new_transformation not in self.column_transformations[current_column]:
                self.column_transformations[current_column].append(new_transformation)
                self.window["-TRANSFORMATIONS-"].update(values=self.column_transformations[current_column])
            else:
                sg.popup_warning("Transformation already exists.")

    def select_algorithm(self):
        # Algorithm selection remains unchanged
        ...

    def run(self):
        while True:
            event, values = self.window.read()
            if event in (sg.WIN_CLOSED, "Exit"):
                break
            elif event == "Load CSV":
                self.load_csv()
            elif event == "Set Columns":
                self.set_columns()
            elif event == "Next":
                if self.y_column:
                    self.next_column()
                else:
                    sg.popup_warning("Please set the column selections first.")
            elif event == "Save Decisions":
                self.save_decisions()
            elif event == "Remove Selected Distribution":
                self.remove_distribution()
            elif event == "Add Distribution":
                self.add_distribution()
            elif event == "Remove Selected Transformation":
                self.remove_transformation()
            elif event == "Add Transformation":
                self.add_transformation()

        self.window.close()

if __name__ == "__main__":
    app = DecisionApp()
    app.run()