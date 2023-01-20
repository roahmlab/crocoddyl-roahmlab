///////////////////////////////////////////////////////////////////////////////
// BSD 3-Clause License
//
// Copyright (C) 2019-2023, LAAS-CNRS, University of Edinburgh,
//                          Heriot-Watt University
// Copyright note valid unless otherwise stated in individual files.
// All rights reserved.
///////////////////////////////////////////////////////////////////////////////

#include "crocoddyl/core/residuals/control.hpp"
#include "crocoddyl/core/utils/exception.hpp"

namespace crocoddyl {

template <typename Scalar>
ResidualModelControlTpl<Scalar>::ResidualModelControlTpl(boost::shared_ptr<typename Base::StateAbstract> state,
                                                         const VectorXs& uref)
    : Base(state, static_cast<std::size_t>(uref.size()), static_cast<std::size_t>(uref.size()), false, false, true),
      uref_(uref) {
  if (nu_ == 0) {
    throw_pretty("Invalid argument: "
                 << "it seems to be an autonomous system, if so, don't add this residual function");
  }
}

template <typename Scalar>
ResidualModelControlTpl<Scalar>::ResidualModelControlTpl(boost::shared_ptr<typename Base::StateAbstract> state,
                                                         const std::size_t nu)
    : Base(state, nu, nu, false, false, true), uref_(VectorXs::Zero(nu)) {
  if (nu_ == 0) {
    throw_pretty("Invalid argument: "
                 << "it seems to be an autonomous system, if so, don't add this residual function");
  }
}

template <typename Scalar>
ResidualModelControlTpl<Scalar>::ResidualModelControlTpl(boost::shared_ptr<typename Base::StateAbstract> state)
    : Base(state, state->get_nv(), state->get_nv(), false, false, true), uref_(VectorXs::Zero(state->get_nv())) {}

template <typename Scalar>
ResidualModelControlTpl<Scalar>::~ResidualModelControlTpl() {}

template <typename Scalar>
void ResidualModelControlTpl<Scalar>::calc(const boost::shared_ptr<ResidualDataAbstract>& data,
                                           const Eigen::Ref<const VectorXs>&, const Eigen::Ref<const VectorXs>& u) {
  if (static_cast<std::size_t>(u.size()) != nu_) {
    throw_pretty("Invalid argument: "
                 << "u has wrong dimension (it should be " + std::to_string(nu_) + ")");
  }

  data->r = u - uref_;
}

template <typename Scalar>
void ResidualModelControlTpl<Scalar>::calc(const boost::shared_ptr<ResidualDataAbstract>& data,
                                           const Eigen::Ref<const VectorXs>&) {
  data->r.setZero();
}

template <typename Scalar>
#ifndef NDEBUG
void ResidualModelControlTpl<Scalar>::calcDiff(const boost::shared_ptr<ResidualDataAbstract>& data,
                                               const Eigen::Ref<const VectorXs>&, const Eigen::Ref<const VectorXs>&) {
#else
void ResidualModelControlTpl<Scalar>::calcDiff(const boost::shared_ptr<ResidualDataAbstract>&,
                                               const Eigen::Ref<const VectorXs>&, const Eigen::Ref<const VectorXs>&) {
#endif
  // The Jacobian has constant values which were set in createData.
  assert_pretty(MatrixXs(data->Ru).isApprox(MatrixXs::Identity(nu_, nu_)), "Ru has wrong value");
}

template <typename Scalar>
boost::shared_ptr<ResidualDataAbstractTpl<Scalar> > ResidualModelControlTpl<Scalar>::createData(
    DataCollectorAbstract* const _data) {
  boost::shared_ptr<ResidualDataAbstract> data =
      boost::allocate_shared<ResidualDataAbstract>(Eigen::aligned_allocator<ResidualDataAbstract>(), this, _data);
  data->Ru.diagonal().fill((Scalar)1.);
  return data;
}

template <typename Scalar>
void ResidualModelControlTpl<Scalar>::print(std::ostream& os) const {
  os << "ResidualModelControl";
}

template <typename Scalar>
const typename MathBaseTpl<Scalar>::VectorXs& ResidualModelControlTpl<Scalar>::get_reference() const {
  return uref_;
}

template <typename Scalar>
void ResidualModelControlTpl<Scalar>::set_reference(const VectorXs& reference) {
  if (static_cast<std::size_t>(reference.size()) != nu_) {
    throw_pretty("Invalid argument: "
                 << "the control reference has wrong dimension (" << reference.size()
                 << " provided - it should be " + std::to_string(nu_) + ")")
  }
  uref_ = reference;
}

}  // namespace crocoddyl
