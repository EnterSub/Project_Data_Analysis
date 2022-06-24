import os, random, shutil, cv2
from tensorflow.keras.utils import Sequence
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Conv2D, Flatten, Dense, MaxPool2D, GlobalAveragePooling2D, Dropout
from tensorflow.keras.callbacks import ModelCheckpoint, LearningRateScheduler
from os import listdir
import numpy as np
import tensorflow as tf

# 0 – Б
# 1 – Н
# 2 – О

for i in range(3):  # Count of classes
    index_number = i
    data = f'{os.getcwd()}//DATA//{i}'
    input_files = os.listdir(data)
    for index, file in enumerate(input_files):
        try:
            os.rename(os.path.join(data, file), os.path.join(data, f'{index_number}({index}).png'))
        except FileExistsError:
            pass

# Image channels
for i in range(3):  # Count of classes
    index_number = i
    data = f'{os.getcwd()}//DATA//{i}'
    input_files = os.listdir(data)
    for index, file in enumerate(input_files):
        img = cv2.imread(os.path.join(data, file), 0)
        cv2.imwrite(os.path.join(data, file), img)

# Process files to train, test and validation sub-folders
for i in ['TEST', 'TRAIN', 'VALIDATION']:
    try:
        os.mkdir(i)
    except FileExistsError:
        pass

for i in range(3):
    for j in ['TEST', 'TRAIN', 'VALIDATION']:
        try:
            os.mkdir(os.path.join(j, str(i)))
        except FileExistsError:
            pass

def calculate():
    for i in range(3):  # Count of classes
        index_number = i
        train = fr'{os.getcwd()}//TRAIN//{i}'
        test = fr'{os.getcwd()}//TEST//{i}'
        validation = fr'{os.getcwd()}//VALIDATION//{i}'

        onlyfiles = [f for f in os.listdir(train) if os.path.isfile(os.path.join(train, f))]
        no_of_files = round((len(onlyfiles) / 8))  # 12,5%

        print(f'Class: {i}, Train: {len(onlyfiles)}, Moving: {no_of_files}')

        def to_test():
            for count, i in enumerate(range(no_of_files), 1):
                files = [filenames for (filenames) in os.listdir(train)]
                random_file = random.choice(files)
                try:
                    shutil.move(os.path.join(train, random_file), test)
                except Exception:
                    pass

            files_test = os.listdir(test)
            for index, file in enumerate(files_test):
                try:
                    os.rename(os.path.join(test, file), os.path.join(test, f'{index_number}({index}).png'))
                except FileExistsError:
                    pass
            return count, len(onlyfiles)

        to_test()

        def to_validation():
            for count, i in enumerate(range(no_of_files), 1):
                files = [filenames for (filenames) in os.listdir(train)]
                random_file = random.choice(files)
                try:
                    shutil.move(os.path.join(train, random_file), validation)
                except Exception:
                    pass

            files_validation = os.listdir(validation)
            for index, file in enumerate(files_validation):
                try:
                    os.rename(os.path.join(validation, file), os.path.join(validation, f'{index_number}({index}).png'))
                except FileExistsError:
                    pass

            files_train = os.listdir(train)
            for index, file in enumerate(files_train):
                try:
                    os.rename(os.path.join(train, file), os.path.join(train, f'{index_number}({index}).png'))
                except FileExistsError:
                    pass
            return count, len(onlyfiles)

        to_validation()


calculate()

for i in range(3):  # Count of classes
    index_number = i
    for j in ['TRAIN', 'TEST', 'VALIDATION']:
        data = fr'{os.getcwd()}//{j}//{i}'
        input_files = os.listdir(data)
        for index, file in enumerate(input_files):
            try:
                os.rename(os.path.join(data, file), os.path.join(data, f'{index_number}({index}).png'))
            except FileExistsError:
                pass


# Count minimum of files in sub-folder
def count_minimum_files():
    onlyfiles_train, onlyfiles_test, min_files_validate = 0, 0, 0
    min_files_train, min_files_test, min_files_validate = [], [], []
    for count, i in enumerate(range(3), 1):  # Count of classes
        train = fr'{os.getcwd()}//TRAIN//{i}'
        test = fr'{os.getcwd()}//TEST//{i}'
        validate = fr'{os.getcwd()}//VALIDATION//{i}'
        try:
            onlyfiles_train = [f for f in os.listdir(train) if os.path.isfile(os.path.join(train, f))]
        except Exception:
            pass

        try:
            onlyfiles_test = [f for f in os.listdir(test) if os.path.isfile(os.path.join(test, f))]
        except Exception:
            pass

        try:
            onlyfiles_validate = [f for f in os.listdir(validate) if os.path.isfile(os.path.join(validate, f))]
        except Exception:
            pass

        try:
            min_files_train.append(len(onlyfiles_train))
        except Exception:
            min_files_train.append(0)

        try:
            min_files_test.append(len(onlyfiles_test))
        except Exception:
            min_files_test.append(0)

        try:
            min_files_validate.append(len(onlyfiles_validate))
        except Exception:
            min_files_validate.append(0)
    print(f'Train: {min(min_files_train)}, Test: {min(min_files_test)}, Validation: {min(min_files_validate)}')
    print()
    for count, (i, j, k) in enumerate(zip(min_files_train, min_files_test, min_files_validate), 0):
        print(f'Class: {count}, Trains: {i}, Tests: {j}, Validations: {k}')
    return i, j, k


COUNT_TRAIN_IMAGE, COUNT_VALID_IMAGE, COUNT_TEST_IMAGE = count_minimum_files()

directory_train_data_base = 'TRAIN'
directory_valid_data_base = 'VALIDATION'
directory_test_data_base = 'TEST'

COUNT_CLASS = 3  # Count of classes
COUNT_EPOCH = 20  # Epoch count


class GeneratorImage(Sequence):
    """Class for generating packages of test images"""

    def __init__(self):
        self.Y = np.eye(COUNT_CLASS)

    def __len__(self):
        return COUNT_TRAIN_IMAGE

    def __getitem__(self, index):
        index += 1
        list_array_images = []
        list_file = listdir(directory_train_data_base)
        for file in list_file:
            im = cv2.imread(f'{directory_train_data_base}\\{file}\\{file}({index}).png', 0)
            im = np.float32(im)
            im /= 255
            list_array_images.append(np.array(im))

        return np.array(list_array_images, dtype=np.float32), self.Y


class GeneratorValidImage(Sequence):
    """Class for generating packages of test images"""

    def __init__(self):
        self.Y = np.eye(COUNT_CLASS)

    def __len__(self):
        return COUNT_VALID_IMAGE

    def __getitem__(self, index):
        index += 1
        list_array_images = []
        list_file = listdir(directory_valid_data_base)
        for file in list_file:
            im = cv2.imread(f'{directory_valid_data_base}\\{file}\\{file}({index}).png', 0)
            im = np.float32(im)
            im /= 255
            list_array_images.append(np.array(im))

        return np.array(list_array_images, dtype=np.float32), self.Y


class GeneratorTestImage(Sequence):
    """Class for generating packages of test images"""

    def __init__(self):
        self.Y = np.eye(COUNT_CLASS)

    def __len__(self):
        return COUNT_TEST_IMAGE

    def __getitem__(self, index):
        index += 1
        list_array_images = []
        list_file = listdir(directory_test_data_base)
        for file in list_file:
            im = cv2.imread(f'{directory_test_data_base}\\{file}\\{file}({index}).png', 0)
            im = np.float32(im)
            im /= 255
            list_array_images.append(np.array(im))

        return np.array(list_array_images, dtype=np.float32), self.Y


def create_model():
    """Function for creating a model"""

    # Creating sequential model
    new_model = Sequential()

    # Add layers to the model
    new_model.add(Conv2D(32, kernel_size=2, strides=2, activation='relu', input_shape=(145, 145, 1)))
    new_model.add(Conv2D(128, kernel_size=2, strides=2, activation='relu'))

    new_model.add(MaxPool2D((2, 2)))

    new_model.add(Conv2D(512, kernel_size=3, activation='relu'))

    new_model.add(Flatten())
    new_model.add(Dense(3, activation='softmax'))  # Count of classes

    new_model.summary()

    new_model.compile('adam', 'categorical_crossentropy', metrics=['accuracy'])

    generator = GeneratorImage()

    generator_valid = GeneratorValidImage()

    new_model.fit(generator, epochs=COUNT_EPOCH, validation_data=generator_valid, steps_per_epoch=COUNT_TRAIN_IMAGE,
                  shuffle=True, callbacks=[ModelCheckpoint('MODELS\\model_example.h5', save_best_only=True)])

    return new_model


# Creating model
new_model = create_model()

tf.keras.utils.plot_model(
    new_model,
    to_file="model.png",
    show_shapes=True,
    show_dtype=False,
    show_layer_names=True,
    rankdir="TB",
    expand_nested=False,
    dpi=96,
    layer_range=None,
    show_layer_activations=True,
)

# Export model
keras_file = 'MODELS\\model.h5'
tf.keras.models.save_model(model, keras_file)
model = tf.keras.models.load_model('MODELS\\model.h5')
converter = tf.lite.TFLiteConverter.from_keras_model(model)
converter.experimental_new_converter = True
tflite_model = converter.convert()
open("MODELS\\converted_model.tflite", "wb").write(tflite_model)
