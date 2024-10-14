#include <pybind11/pybind11.h>

namespace py = pybind11;
typedef py::call_guard<py::gil_scoped_release> release_gil;

#include <wpinet/PortForwarder.h>

PYBIND11_TYPE_CASTER_BASE_HOLDER(
    typename wpi::PortForwarder,
    std::unique_ptr<typename wpi::PortForwarder, py::nodelete>);

PYBIND11_MODULE(port, m) {

  py::class_<typename wpi::PortForwarder,
             std::unique_ptr<typename wpi::PortForwarder, py::nodelete>>
      cls_PortForwarder(m, "PortForwarder");

  cls_PortForwarder.doc() = "Forward ports to another host.  This is "
                            "primarily useful for accessing\n"
                            "Ethernet-connected devices from a computer "
                            "tethered to the RoboRIO USB port.";

  cls_PortForwarder

      .def_static(
          "getInstance", &wpi::PortForwarder::GetInstance, release_gil(),
          py::return_value_policy::reference,
          py::doc("Get an instance of the PortForwarder class.\n"
                  "\n"
                  "This is a singleton to guarantee that there is only a "
                  "single instance\n"
                  "regardless of how many times GetInstance is called."))

      .def("add", &wpi::PortForwarder::Add, py::arg("port"),
           py::arg("remoteHost"), py::arg("remotePort"), release_gil(),
           py::doc("Forward a local TCP port to a remote host and port.\n"
                   "Note that local ports less than 1024 won't work as a "
                   "normal user.\n"
                   "\n"
                   ":param port:       local port number\n"
                   ":param remoteHost: remote IP address / DNS name\n"
                   ":param remotePort: remote port number"))

      .def("remove", &wpi::PortForwarder::Remove, py::arg("port"),
           release_gil(),
           py::doc("Stop TCP forwarding on a port.\n"
                   "\n"
                   ":param port: local port number"))

      ;
}