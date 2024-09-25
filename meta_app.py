from pickle import FALSE

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

        layout = [
            [sg.Text("Load a CSV file to continue.")],
            [sg.Button("Load CSV")],
            [sg.Text("", size=(40, 1), key="-MESSAGE-")],
            [sg.Text("Grouped Column: "), sg.Combo(["None"], key="-GROUPED-")],
            [sg.Text("Panel Column: "), sg.Combo(["None"], key="-PANEL-")],
            [sg.Text("Y Column: "), sg.Combo([], key="-Y-")],
            [sg.Button("Set Columns"), sg.Button("Next"), sg.Button("Save Decisions", disabled=True)],
            [sg.Text("Current Column: ", size=(20, 1)), sg.Text("", key="-CURRENT-COLUMN-")],
            [sg.Text("", size=(20, 1), key="-DISPLAY-COLUMN-")],
            [sg.Text("", size=(40, 1), key="-COLUMN-INFO-")],
            [
                sg.Listbox(values=[], select_mode=sg.LISTBOX_SELECT_MODE_MULTIPLE, key="-DISTRIBUTIONS-", size=(30, 6)),
                sg.Button("Remove Selected Distribution", disabled=True),
                sg.Button("Add Distribution", disabled=True)
            ],
            [
                sg.Listbox(values=[], select_mode=sg.LISTBOX_SELECT_MODE_MULTIPLE, key="-TRANSFORMATIONS-",
                           size=(30, 6)),
                sg.Button("Remove Selected Transformation", disabled=True),
                sg.Button("Add Transformation", disabled=True)
            ],
            [sg.Checkbox("Level 1", key="-LEVEL1-", default=True), sg.Text("Off")],
            [sg.Checkbox("Level 2", key="-LEVEL2-", default=True), sg.Text("Fixed Effects")],
            [sg.Checkbox("Level 3", key="-LEVEL3-", default=True), sg.Text("Random Parameters")],
            [sg.Checkbox("Level 4", key="-LEVEL4-", default=True), sg.Text("Correlated Random Parameters in Means")],
            [sg.Checkbox("Level 5", key="-LEVEL5-", disabled=True), sg.Text("Grouped Random Parameters")],
            [sg.Checkbox("Level 6", key="-LEVEL6-", default=True), sg.Text("Heterogeneity in Means")],
            [sg.Button('Setup Hyper-Pararameters')]
        ]

        self.window = sg.Window("Decision Maker", layout)

    def load_csv(self):
        file_path = sg.popup_get_file("Select a CSV file", file_types=(("CSV Files", "*.csv"),))
        if file_path:
            try:
                self.data = pd.read_csv(file_path, encoding='utf-8', on_bad_lines='warn')
                self.current_index = 0
                self.decisions = []

                self.column_names = self.data.columns.tolist()

                self.window["-Y-"].update(values=self.column_names)
                self.window["-GROUPED-"].update(values=["None"] + self.column_names)
                self.window["-PANEL-"].update(values=["None"] + self.column_names)

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

            if current_column not in self.column_distributions:
                self.column_distributions[current_column] = ["Normal", "Triangular", "Uniform"]

            self.window["-DISTRIBUTIONS-"].update(values=self.column_distributions[current_column])

            if current_column not in self.column_transformations:
                self.column_transformations[current_column] = []

            self.window["-TRANSFORMATIONS-"].update(values=self.column_transformations[current_column])

            self.window["Remove Selected Distribution"].update(disabled=False)
            self.window["Add Distribution"].update(disabled=False)
            self.window["Remove Selected Transformation"].update(disabled=False)
            self.window["Add Transformation"].update(disabled=False)

            for i in range(1, 7):
                self.window[f"-LEVEL{i}-"].update(True)

            if self.grouped_column == "None":
                self.window["-LEVEL5-"].update(disabled=True)
            else:
                self.window["-LEVEL5-"].update(disabled=False)

            if self.current_index == len(self.columns_to_process) - 1:
                self.window["Save Decisions"].update(disabled=False)

            self.window["-MESSAGE-"].update(f"Processing column: {current_column}...")
        else:
            sg.popup("End", "No more columns to process!")

    def next_column(self):
        if self.current_index < len(self.columns_to_process):
            decisions = [self.window[f"-LEVEL{i}-"].get() for i in range(1, 7)]
            current_column = self.columns_to_process[self.current_index]
            distributions = self.column_distributions[current_column]
            transformations = self.column_transformations[current_column]
            self.decisions.append((current_column, *decisions, distributions, transformations))
            self.current_index += 1
            self.show_column()
        else:
            sg.popup("End", "No more columns to process!")

    def save_decisions(self):
        if self.decisions:
            output_df = pd.DataFrame(self.decisions,
                                     columns=["Column"] + [f"Level {i}" for i in range(1, 7)] + ["Distributions",
                                                                                                 "Transformations"])
            output_file_path = sg.popup_get_file("Save decisions as", save_as=True,
                                                 file_types=(("CSV Files", "*.csv"),))
            if output_file_path:
                output_df.to_csv(output_file_path, index=False)
                sg.popup("Success", "Decisions saved successfully!")
                self.open_hyperparameter_window()
        else:
            sg.popup_warning("Warning", "No decisions to save!")

    def open_algorithm_hyperparameter_window(self):
        # Initial layout with default parameters for Simulated Annealing (SA)
        layout = [
            [sg.Text("Select Algorithm:")],
            [sg.Radio("Simulated Annealing (SA)", "ALGORITHM", enable_events=True,key="-SA-", default=True)],
            [sg.Radio("Differential Evolution (DE)", "ALGORITHM", enable_events=True,key="-DE-")],
            [sg.Radio("Hill Climbing (HS)", "ALGORITHM", enable_events=True,key="-HS-")],
            [sg.Text("Set Hyperparameters:", key  = "-BLAH-")],
            [sg.Column(self.get_algorithm_hyperparameters("SA"), key="-PARAMS-"), sg.Column(self.get_algorithm_hyperparameters("DE"), key="-PARAMSDE-", visible = False)
             ,sg.Column(self.get_algorithm_hyperparameters("HS"), key="-PARAMSHS-", visible = False)],  # Default to SA parameters

            [sg.Button("Save Algorithm Parameters"), sg.Button("Cancel")]
        ]

        algorithm_window = sg.Window("Algorithm Hyperparameters", layout, finalize=True)

        while True:
            event, values = algorithm_window.read()

            # Check if a radio button was clicked
            if event in ("-SA-", "-DE-", "-HS-"):
                if event == '-DE-':
                    algorithm_window["-PARAMS-"].Update(visible=False)
                    algorithm_window["-PARAMSDE-"].Update(visible = True)
                    algorithm_window["-PARAMSHS-"].Update(visible=False)
                elif event == '-SA-':
                    algorithm_window["-PARAMS-"].Update(visible=True)
                    algorithm_window["-PARAMSDE-"].Update(visible=False)
                    algorithm_window["-PARAMSHS-"].Update(visible=False)
                elif event == '-HS-':
                    algorithm_window["-PARAMS-"].Update(visible=False)
                    algorithm_window["-PARAMSDE-"].Update(visible=False)
                    algorithm_window["-PARAMSHS-"].Update(visible=True)







            if event in (sg.WIN_CLOSED, "Cancel"):
                break

            if event == "Save Algorithm Parameters":
                self.save_algorithm_parameters(values)

        algorithm_window.close()

    def get_algorithm_hyperparameters(self, algorithm):
        """ Returns the layout for the hyperparameters based on the selected algorithm. """

        print(algorithm)
        if algorithm == "SA":
            return [
                [sg.Text("Initial Number of Solutions for Probability Acceptance:"),
                 sg.Slider(range=(1, 100), default_value=50, orientation='h', key="-SLNS-")]
                [sg.Text("Initial Acceptance Probability:"), sg.Slider(range=(1, 100), default_value=50, orientation='h', key="-TEMP-")],
                [sg.Text("Crossover Rate:"), sg.Slider(range=(0.01, 1), default_value=0.3, orientation='h', key="-CROSSOVER-")],
                [sg.Text("Cooling Rate:"),
                 sg.Slider(range=(0.01, 1), resolution=0.01, default_value=0.95, orientation='h', key="-COOLING_RATE-")],
                [sg.Text("Mutation Rate:"),
                sg.Slider(range=(0.01, 1), resolution=0.01, default_value=0.2, orientation='h', key="-COOLING_RATE-")]
            ]
        elif algorithm == "DE":
            return [
                [sg.Text("Crossover Rate:"),
                 sg.Slider(range=(0.0, 1.0), resolution=0.01, default_value=0.8, orientation='h', key="-CROSSOVER-")],
                [sg.Text("Mutation Rate:"),
                 sg.Slider(range=(0.01, 1), resolution=0.01, default_value=0.2, orientation='h', key="-COOLING_RATE-")],
                [sg.Text("Pitch Adjustment Range:"),
                 sg.Slider(range=(1, 5), default_value=1, orientation='h', key="-PITCH-")],
                [sg.Text("Population Size:"),
                 sg.Slider(range=(5, 100), default_value=20, orientation='h', key="-POP_SIZE-")]
            ]
        elif algorithm == "HS":

            return [
                [sg.Text("Harmony Memory Size:"),
                 sg.Slider(range=(5, 100), default_value=20, orientation='h', key="-HMS-")],
                [sg.Text("HMCR:"),
                 sg.Slider(range=(0.0, 1.0), resolution=0.01, default_value=0.9, orientation='h', key="-HMCR-")],
                [sg.Text("Pitch Adjustment Rate:"),
                 sg.Slider(range=(0.0, 1.0), resolution=0.01, default_value=0.5, orientation='h', key="-PAI-")]
                [sg.Text("Pitch Adjustment Range:"),
                sg.Slider(range=(1, 5), default_value=1, orientation='h', key="-PITCH-")]
            ]

    def save_algorithm_parameters(self, values):
        algorithm_params = {
            "Algorithm": "SA" if values["-SA-"] else "DE" if values["-DE-"] else "HS",
            "Temperature": values.get("-TEMP-", None),
            "Cooling Rate": values.get("-COOLING_RATE-", None),
            "Crossover Rate": values.get("-CROSSOVER-", None),
            "Pitch Adjustment": values.get("-PITCH-", None),
            "Population Size": values.get("-POP_SIZE-", None),
            "Harmony Memory Size": values.get("-HMS-", None),
            "HMCR": values.get("-HMCR-", None),
            "Pitch Adjustment Rate": values.get("-PAI-", None)
        }
        # Save or process the algorithm parameters as needed
        print("Algorithm Parameters:", algorithm_params)
        sg.popup("Algorithm parameters saved successfully!")

    # Call this method from the appropriate place in your existing code
    # For example, after saving hyperparameters or wherever logical


    def open_hyperparameter_window(self):
        layout = [
            [sg.Text("Select Model Types (Hold Ctrl to select multiple):")],
            [sg.Listbox(values=["Poisson", "Negative Binomial"], select_mode=sg.LISTBOX_SELECT_MODE_MULTIPLE,
                        key="-MODEL_TYPE-")],
            [sg.Text("Select Objective:")],
            [sg.Radio("Single Objective", "OBJECTIVE", enable_events=True,key="-SINGLE-OBJECTIVE-", default=True)],
            [sg.Radio("Multi-Objective", "OBJECTIVE", enable_events=True,key="-MULTI-OBJECTIVE-")],
            [sg.Text("Select Primary Objective Metric:")],
            [sg.Combo(["BIC", "AIC", "RMSE"], key="-OBJECTIVE_METRIC-")],
            [sg.Text("Select Secondary Objective Metric:")],
            [sg.Combo(["BIC", "AIC", "RMSE"], key="-SECOND_OBJECTIVE_METRIC-", disabled=True)],
            [sg.Text("MAXTIME (seconds):"), sg.InputText("240000", key="-MAXTIME-"),
             sg.Button("?", tooltip="Time in seconds.")],
            [sg.Text("Number of Iterations without Improvement:"),
             sg.Slider(range=(1, 1000), default_value=100, orientation='h', key="-ITERATIONS-")],
            [sg.Text("Do you want a validation split?"),
             sg.Radio("Yes", "VALIDATION", key="-VALIDATION-YES-", default=False),
             sg.Radio("No", "VALIDATION", key="-VALIDATION-NO-", default=True)],
            [sg.Text("Train Split (%):"), sg.InputText("80", key="-TRAIN_SPLIT-", disabled=True)],
            [sg.Text("Validation Split (%):"), sg.InputText("10", key="-VALIDATION_SPLIT-", disabled=True)],
            [sg.Text("Test Split (%):"), sg.InputText("10", key="-TEST_SPLIT-", disabled=True)],
            [sg.Button("Save Hyperparameters"), sg.Button("Cancel")]
        ]

        hyper_window = sg.Window("Hyperparameter Setup", layout, finalize=True)

        # Initial state setup
        hyper_window["-SECOND_OBJECTIVE_METRIC-"].update(disabled=True)
        hyper_window["-TRAIN_SPLIT-"].update(disabled=True)
        hyper_window["-VALIDATION_SPLIT-"].update(disabled=True)
        hyper_window["-TEST_SPLIT-"].update(disabled=True)

        while True:
            event, values = hyper_window.read()
            print(event)
            # Check for radio button changes
            if event in ("-SINGLE-OBJECTIVE-", "-MULTI-OBJECTIVE-"):
                # Enable/disable secondary objective metric dropdown
                hyper_window["-SECOND_OBJECTIVE_METRIC-"].update(disabled=not values["-MULTI-OBJECTIVE-"])

                # Enable/disable train, validation, and test split inputs
                if values["-MULTI-OBJECTIVE-"]:
                    hyper_window["-TRAIN_SPLIT-"].update(disabled=False)
                    hyper_window["-VALIDATION_SPLIT-"].update(disabled=False)
                    hyper_window["-TEST_SPLIT-"].update(disabled=False)
                else:
                    hyper_window["-TRAIN_SPLIT-"].update(disabled=True, value="80")
                    hyper_window["-VALIDATION_SPLIT-"].update(disabled=True, value="10")
                    hyper_window["-TEST_SPLIT-"].update(disabled=True, value="10")

            # Enable/disable validation split inputs based on selection
            if values["-VALIDATION-YES-"]:
                hyper_window["-VALIDATION_SPLIT-"].update(disabled=False)
                hyper_window["-TEST_SPLIT-"].update(disabled=False)
            else:
                hyper_window["-VALIDATION_SPLIT-"].update(disabled=True, value="0")
                hyper_window["-TEST_SPLIT-"].update(disabled=True, value="100")

            if event in (sg.WIN_CLOSED, "Cancel"):
                break

            if event == "Save Hyperparameters":
                self.save_hyperparameters(values)

        hyper_window.close()

    def save_hyperparameters(self, values):
        hyperparameters = {
            "Model Types": values["-MODEL_TYPE-"],
            "Objective Type": "Single" if values["-SINGLE-OBJECTIVE-"] else "Multi",
            "Primary Objective Metric": values["-OBJECTIVE_METRIC-"],
            "Secondary Objective Metric": values["-SECOND_OBJECTIVE_METRIC-"] if values["-MULTI-OBJECTIVE-"] else None,
            "MAXTIME": values["-MAXTIME-"],
            "Iterations": values["-ITERATIONS-"],
            "Train Split": values["-TRAIN_SPLIT-"],
            "Validation Split": values["-VALIDATION_SPLIT-"] if values["-VALIDATION-YES-"] else "0",
            "Test Split": values["-TEST_SPLIT-"] if values["-VALIDATION-YES-"] else "100"
        }
        df = pd.DataFrame([hyperparameters])
        df.to_csv("setup_hyper.csv", index=False)
        sg.popup("Hyperparameters saved as setup_hyper.csv")

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
            elif event == 'Setup Hyper-Pararameters':
                self.open_algorithm_hyperparameter_window()

        self.window.close()


if __name__ == "__main__":
    app = DecisionApp()
    app.run()