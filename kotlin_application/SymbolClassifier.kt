/* The fundamental package from The TensorFlow Authors */
package org.tensorflow.lite.codelabs.digitclassifier
import android.content.Context
import android.content.res.AssetManager
import android.graphics.Bitmap
import android.util.Log
import com.google.android.gms.tasks.Task
import com.google.android.gms.tasks.TaskCompletionSource
import java.io.FileInputStream
import java.io.IOException
import java.nio.ByteBuffer
import java.nio.ByteOrder
import java.nio.channels.FileChannel
import java.util.concurrent.ExecutorService
import java.util.concurrent.Executors
import org.tensorflow.lite.Interpreter

class SymbolDigitizer(private val context: Context) {
  private var interpreter: Interpreter? = null
  var isInitialized = false
    private set

  private val executorService: ExecutorService = Executors.newCachedThreadPool()
  private var inputImageWidth: Int = 0
  private var inputImageHeight: Int = 0
  private var modelInputSize: Int = 0

  fun initialize(): Task<Void> {
    val task = TaskCompletionSource<Void>()
    executorService.execute {
      try {
        initializeInterpreter()
        task.setResult(null)
      } catch (e: IOException) {
        task.setException(e)
      }
    }
    return task.task
  }

  @Throws(IOException::class)
  private fun initializeInterpreter() {
    val assetManager = context.assets
    val model = loadModelFile(assetManager, "converted_model.tflite") // Load the TF Lite model from asset folder
    val options = Interpreter.Options()
    options.setUseNNAPI(true)
    val interpreter = Interpreter(model, options)
    // Read input shape from model file.
    val inputShape = interpreter.getInputTensor(0).shape()
    inputImageWidth = inputShape[1]
    inputImageHeight = inputShape[2]
    modelInputSize = FLOAT_TYPE_SIZE * inputImageWidth *
      inputImageHeight * PIXEL_SIZE
    // Finish interpreter initialization.
    this.interpreter = interpreter
    isInitialized = true
    Log.d(TAG, "Initialized TFLite interpreter.")
  }

  @Throws(IOException::class)
  private fun loadModelFile(assetManager: AssetManager, filename: String): ByteBuffer {
    val fileDescriptor = assetManager.openFd(filename)
    val inputStream = FileInputStream(fileDescriptor.fileDescriptor)
    val fileChannel = inputStream.channel
    val startOffset = fileDescriptor.startOffset
    val declaredLength = fileDescriptor.declaredLength
    return fileChannel.map(FileChannel.MapMode.READ_ONLY, startOffset, declaredLength)
  }

  private fun classify(bitmap: Bitmap): String {
    check(isInitialized) { "TF Lite Interpreter is not initialized yet." }

    // Pre-processing: resize the input image to match the model input shape.
    val resizedImage = Bitmap.createScaledBitmap(
      bitmap,
      inputImageWidth,
      inputImageHeight,
      true
    )
    val byteBuffer = convertBitmapToByteBuffer(resizedImage)
    // Define an array to store the model output.
    val output = Array(1) { FloatArray(OUTPUT_CLASSES_COUNT) }
    // Run inference with the input data.
    interpreter?.run(byteBuffer, output)
    // Post-processing: find the digit that has the highest probability like string.
    val result = output[0]
    var class_output = "Nothing"
    val maxIndex = result.indices.maxByOrNull { result[it] } ?: -1

    if (maxIndex == 0 && result[maxIndex].toDouble() >= 0.75)
      class_output = "Б"
    if (maxIndex == 1 && result[maxIndex].toDouble() >= 0.75)
      class_output = "Н"
    if (maxIndex == 2 && result[maxIndex].toDouble() >= 0.75)
      class_output = "О"

    val resultString =
      "Result: %s\nPrecision: %2f"
        .format(class_output, result[maxIndex])

    return resultString
  }

  fun classifyAsync(bitmap: Bitmap): Task<String> {
    val task = TaskCompletionSource<String>()
    executorService.execute {
      val result = classify(bitmap)
      task.setResult(result)
    }
    return task.task
  }

  fun close() {
    executorService.execute {
      interpreter?.close()
      Log.d(TAG, "Closed TFLite interpreter.")
    }
  }

  private fun convertBitmapToByteBuffer(bitmap: Bitmap): ByteBuffer {
    val byteBuffer = ByteBuffer.allocateDirect(modelInputSize)
    byteBuffer.order(ByteOrder.nativeOrder())
    val pixels = IntArray(inputImageWidth * inputImageHeight)
    bitmap.getPixels(pixels, 0, bitmap.width, 0, 0, bitmap.width, bitmap.height)

    for (pixelValue in pixels) {
      val r = (pixelValue shr 16 and 0xFF)
      val g = (pixelValue shr 8 and 0xFF)
      val b = (pixelValue and 0xFF)
      // Convert RGB to grayscale and normalize pixel value to [0..1].
      val normalizedPixelValue = (r + g + b) / 3.0f / 255.0f
      byteBuffer.putFloat(normalizedPixelValue)
    }
    return byteBuffer
  }

  companion object {
    private const val TAG = "SymbolClassifier"
    private const val FLOAT_TYPE_SIZE = 4
    private const val PIXEL_SIZE = 1
    private const val OUTPUT_CLASSES_COUNT = 3 //Classes + 1
  }
}
