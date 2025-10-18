#include <rclcpp/rclcpp.hpp>
#include <image_transport/image_transport.hpp>
#include <cv_bridge/cv_bridge.hpp>
#include <opencv2/opencv.hpp>

#include <DarkHelp.hpp>
#include <darkhelp_msgs/msg/bounding_box.hpp>
#include <darkhelp_msgs/msg/bounding_boxes.hpp>
#include <sensor_msgs/msg/image.hpp>

class DarkHelpNode : public rclcpp::Node
{
public:
    DarkHelpNode()
        : Node("darkhelp_node")
    {
        // cargar modelo DarkHelp
        std::string cfg_file   = "/home/ubuntu/pos2/pos2.cfg";
        std::string weights    = "/home/ubuntu/pos2/pos2_best.weights";
        std::string names_file = "/home/ubuntu/pos2/pos2.names";

        darkhelp_ = std::make_unique<DarkHelp::NN>(cfg_file, weights, names_file);
        last_time_ = this->now();
    }

    void init_transport()
    {
        it_ = std::make_shared<image_transport::ImageTransport>(rclcpp::Node::shared_from_this());

        sub_ = it_->subscribe(
            "/ros2/image_topic",
            1,
            std::bind(&DarkHelpNode::imageCallback, this, std::placeholders::_1)
        );

        pub_boxes_ = this->create_publisher<darkhelp_msgs::msg::BoundingBoxes>(
            "/darkhelp/bounding_boxes",
            rclcpp::QoS(10)
        );

        // publicador de imagen procesada (con bounding boxes dibujados)
        pub_image_ = this->create_publisher<sensor_msgs::msg::Image>(
            "/darkhelp/image_out",
            rclcpp::QoS(10)
        );
    }

private:
    void imageCallback(const sensor_msgs::msg::Image::ConstSharedPtr msg)
    {
        try
        {
            // convertir a cv::Mat
            cv::Mat frame = cv_bridge::toCvShare(msg, "bgr8")->image;

            // rotar imagen 90 grados clockwise
            cv::Mat rotated;
            cv::rotate(frame, rotated, cv::ROTATE_90_CLOCKWISE);

            // predecir sobre la imagen rotada
            auto results = darkhelp_->predict(rotated);

            // publicar bounding boxes
            darkhelp_msgs::msg::BoundingBoxes boxes_msg;
            std::string detections_str;
            for (const auto &pred : results)
            {
                darkhelp_msgs::msg::BoundingBox box;
                box.name        = pred.name;
                box.probability = pred.best_probability;
                box.x           = pred.rect.x;       // ya sobre imagen rotada
                box.y           = pred.rect.y;
                box.width       = pred.rect.width;
                box.height      = pred.rect.height;
                boxes_msg.bounding_boxes.push_back(box);

                detections_str += box.name + " (" + std::to_string(box.probability) + ") ";

                RCLCPP_INFO(this->get_logger(),
                    "[ROS2 DEBUG] class=%s | x=%d y=%d w=%d h=%d | img=%dx%d",
                    box.name.c_str(),
                    box.x, box.y, box.width, box.height,
                    rotated.cols, rotated.rows);
            }

            pub_boxes_->publish(boxes_msg);

            // generar imagen anotada sobre imagen rotada
            cv::Mat annotated_img = darkhelp_->annotate();

            // publicar imagen anotada
            sensor_msgs::msg::Image::SharedPtr ros_img_msg = cv_bridge::CvImage(
                msg->header, "bgr8", annotated_img
            ).toImageMsg();
            pub_image_->publish(*ros_img_msg);

            // calcular FPS
            rclcpp::Time now = this->now();
            double elapsed = (now - last_time_).seconds();
            frame_count_++;
            if (elapsed >= 1.0) {
                double fps = frame_count_ / elapsed;
                RCLCPP_INFO(this->get_logger(), "FPS: %.2f | Detections: %s", fps, detections_str.c_str());
                frame_count_ = 0;
                last_time_ = now;
            }
        }
        catch (const std::exception &e)
        {
            RCLCPP_ERROR(this->get_logger(), "Error en imageCallback: %s", e.what());
        }
    }

    std::shared_ptr<image_transport::ImageTransport> it_;
    image_transport::Subscriber sub_;
    rclcpp::Publisher<darkhelp_msgs::msg::BoundingBoxes>::SharedPtr pub_boxes_;
    rclcpp::Publisher<sensor_msgs::msg::Image>::SharedPtr pub_image_;
    std::unique_ptr<DarkHelp::NN> darkhelp_;

    int frame_count_ = 0;
    rclcpp::Time last_time_;
};

int main(int argc, char **argv)
{
    rclcpp::init(argc, argv);
    auto node = std::make_shared<DarkHelpNode>();
    node->init_transport();  
    rclcpp::spin(node);
    rclcpp::shutdown();
    return 0;
}
